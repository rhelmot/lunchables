from pathlib import Path
import base64
import json
import logging.handlers
import os
from datetime import datetime, timezone, timedelta
import queue
import socket
import gc

import kubernetes_asyncio.config
import docker_registry_client_async
import coloredlogs
import sonyflake
import aiobotocore.session
import motor.motor_asyncio
from pyeslogging.handlers import PYESHandler as ElasticHandler

from pydatatask.pod_manager import PodManager
from pydatatask.session import Session
from pydatatask.resource_manager import ResourceManager, Resources

session = Session()

incluster = os.getenv("INCLUSTER", "").lower() not in ("0", "", "false")
cron = os.getenv("INCLUSTER_CRON", "").lower() not in ("0", "", "false")

kube_cpu_quota = os.getenv("KUBE_CPU_QUOTA")
kube_mem_quota = os.getenv("KUBE_MEM_QUOTA")
kube_release_name = os.getenv("KUBE_RELEASE_NAME")
assert kube_cpu_quota is not None
assert kube_mem_quota is not None
assert kube_release_name is not None

kube_quota = ResourceManager(
    Resources.parse(cpu=kube_cpu_quota, mem=kube_mem_quota, launches=400)
)

priorities = []
for env, val in os.environ.items():
    if env.startswith("PRIORITY_"):
        directive = json.loads(val)
        if (
            type(directive) is not dict
            or set(directive) - {"priority", "task", "job"}
            or type(directive.get("priority", None)) is not int
        ):
            raise ValueError("Improperly formed priority directive %s" % env)
        priorities.append(directive)


def get_priority(task: str, job: str) -> int:
    result = 0
    for directive in priorities:
        if directive.get("job", job) == job and directive.get("task", task) == task:
            result += directive["priority"]
    return result


@session.resource
async def podman():
    if os.path.exists(
        os.path.expanduser(
            kubernetes_asyncio.config.kube_config.KUBE_CONFIG_DEFAULT_LOCATION
        )
    ):
        await kubernetes_asyncio.config.load_kube_config()
    else:
        kubernetes_asyncio.config.load_incluster_config()
    podman = PodManager(
        app=kube_release_name + "-worker",
        namespace=os.getenv("KUBE_NAMESPACE"),
    )
    yield podman
    await podman.close()


idgen = sonyflake.SonyFlake(datetime(2022, 11, 20, tzinfo=timezone.utc))

shared_mountpoint = Path("/shared")
rwx_path = os.getenv("RWX_PATH")
assert rwx_path is not None
shared_suffix = Path(rwx_path.lstrip("/"))
shared_root = shared_mountpoint / shared_suffix
config_root = Path(__file__).absolute().parent / "yaml"
domain = os.getenv("DOCKER_REGISTRY")
repository = os.getenv("IMAGE_FUZZING")
image_pull_secret = os.getenv("DOCKER_PULL_SECRET")
image_pull_policy = os.getenv("IMAGE_PULL_POLICY")
bucket_secret = os.getenv("BUCKET_SECRET")
rwx_pvc = os.getenv("RWX_PVC")


@session.resource
async def docker():
    with open(Path("~/.docker/config.json").expanduser(), "r") as fp:
        docker_config = json.load(fp)
    username, password = (
        base64.b64decode(docker_config["auths"][domain]["auth"]).decode().split(":")
    )
    registry = docker_registry_client_async.DockerRegistryClientAsync(
        client_session_kwargs={"connector_owner": True},
        tcp_connector_kwargs={"family": socket.AF_INET},
        ssl=True,
    )
    await registry.add_credentials(
        credentials=base64.b64encode(f"{username}:{password}".encode()).decode(),
        endpoint=domain,
    )
    yield registry
    await registry.close()
    gc.collect()


@session.resource
async def minio():
    minio_session = aiobotocore.session.get_session()
    async with minio_session.create_client(
        "s3",
        endpoint_url="http://" + os.getenv("BUCKET_ENDPOINT"),
        aws_access_key_id=os.getenv("BUCKET_USERNAME"),
        aws_secret_access_key=os.getenv("BUCKET_PASSWORD"),
    ) as client:
        yield client


minio_bucket = os.getenv("BUCKET_BUCKET", "")
minio_endpoint = os.getenv("BUCKET_ENDPOINT", "")
assert minio_bucket
assert minio_endpoint
minio_endpoint_incluster = "http://" + os.getenv(
    "BUCKET_ENDPOINT_INCLUSTER", minio_endpoint
)

mongo_url = os.getenv("MONGO_URL")
mongo_secret = os.getenv("MONGO_SECRET")
mongo_database = os.getenv("MONGO_DATABASE")
mongo_url_incluster = os.getenv("MONGO_URL_INCLUSTER", os.getenv("MONGO_URL"))


@session.resource
async def mongo():
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
    collection = client.get_database(mongo_database).get_collection("haccs_pipeline")
    yield collection


coloredlogs.install(level="DEBUG")
logging.root.setLevel("WARNING")
elastic_endpoint = os.getenv("ELASTIC_LOGS_ENDPOINT")
assert elastic_endpoint is not None
eshost, esport = elastic_endpoint.split(":")

es_handler = ElasticHandler(
    hosts=[{"host": eshost, "port": int(esport)}],
    auth_type=ElasticHandler.AuthType.NO_AUTH,
    es_index_name=os.getenv("ELASTIC_LOGS_INDEX"),
    # buffer_size=0,
    # raise_on_indexing_exceptions=True,
)
es_handler.setLevel("DEBUG")
logging.getLogger("pydatatask").setLevel("DEBUG")
log_queue = queue.SimpleQueue()
queue_handler = logging.handlers.QueueHandler(log_queue)
queue_handler.prepare = lambda x: x
queue_listener = logging.handlers.QueueListener(
    log_queue, es_handler, respect_handler_level=True
)


@session.resource
async def es_logging():
    if cron:
        logging.root.addHandler(queue_handler)
        queue_listener.start()
        yield None
        queue_listener.stop()
        es_handler.close()
    else:
        yield None


image_leader = os.getenv("IMAGE_LEADER")
image_greenhouse = os.getenv("IMAGE_GREENHOUSE")
image_rex = os.getenv("IMAGE_REX")
image_gh2fuzz = os.getenv("IMAGE_GH2FUZZ")
image_gh2fuzz_postauth = os.getenv("IMAGE_GH2FUZZ_POSTAUTH")
image_gh2routersploit = os.getenv("IMAGE_GH2ROUTERSPLOIT")
image_rip = os.getenv("IMAGE_RIP")
fuzzer_timeout_str = os.getenv("FUZZER_TIMEOUT_HOURS")
assert fuzzer_timeout_str is not None
fuzzer_timeout = timedelta(hours=float(fuzzer_timeout_str))
