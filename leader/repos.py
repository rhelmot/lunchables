from pydatatask import (
    MongoMetadataRepository,
    S3BucketRepository,
)

# from classes import MountpointDirectoryRepository
from creds import (
    mongo,
    minio,
    minio_bucket,
    minio_endpoint_incluster,
)

targets = MongoMetadataRepository(mongo, "input")
greenhouse_results = S3BucketRepository(
    minio,
    minio_bucket,
    "greenhouse_tars/",
    suffix=".tar.gz",
    mimetype="application/gzip",
    incluster_endpoint=minio_endpoint_incluster,
)
greenhouse_meta = MongoMetadataRepository(mongo, "greenhouse_meta")

greenhouse_logs = S3BucketRepository(
    minio,
    minio_bucket,
    "greenhouse_logs/",
    suffix=".log",
    mimetype="text/plain",
    incluster_endpoint=minio_endpoint_incluster,
)
greenhouse_done = MongoMetadataRepository(mongo, "greenhouse_done")
greenhouse_collect_kube_done = MongoMetadataRepository(
    mongo, "greenhouse_collect_kube_done"
)
greenhouse_collect_func_done = MongoMetadataRepository(
    mongo, "greenhouse_collect_func_done"
)
greenhouse_collect_logs = S3BucketRepository(
    minio,
    minio_bucket,
    "greenhouse_collect_logs/",
    suffix=".log",
    mimetype="text/plain",
    incluster_endpoint=minio_endpoint_incluster,
)


async def ident(x):
    return x


async def is_success(x):
    meta = await greenhouse_meta.info(x)
    if meta.get("result", "") == "SUCCESS":
        return True
    return meta.get("attempts", 0) >= 3


async def is_really_success(x):
    meta = await greenhouse_meta.info(x)
    return meta.get("result", "") == "SUCCESS"


greenhouse_complete = greenhouse_meta.map(ident, is_success)
greenhouse_success = greenhouse_meta.map(ident, is_really_success)

fuzz_logs = S3BucketRepository(
    minio,
    minio_bucket,
    "fuzz_logs/",
    suffix=".log",
    mimetype="text/plain",
    incluster_endpoint=minio_endpoint_incluster,
)
fuzz_done = MongoMetadataRepository(mongo, "fuzz_done")

postauthfuzz_logs = S3BucketRepository(
    minio,
    minio_bucket,
    "postauthfuzz_logs/",
    suffix=".log",
    mimetype="text/plain",
    incluster_endpoint=minio_endpoint_incluster,
)
postauthfuzz_done = MongoMetadataRepository(mongo, "postauthfuzz_done")

routersploit_logs = S3BucketRepository(
    minio,
    minio_bucket,
    "routersploit_logs/",
    suffix=".log",
    mimetype="text/plain",
    incluster_endpoint=minio_endpoint_incluster,
)
routersploit_done = MongoMetadataRepository(mongo, "routersploit_done")
routersploit_results = S3BucketRepository(
    minio,
    minio_bucket,
    "routersploit_tars/",
    suffix=".tar.gz",
    mimetype="application/gzip",
    incluster_endpoint=minio_endpoint_incluster,
)

# fuzzing_min_results = MountpointDirectoryRepository(  # TODO
#    pipeline_mountpoint, pipeline_suffix / "phase3" / "output"
# )

rip_logs = S3BucketRepository(
    minio,
    minio_bucket,
    "rip_logs/",
    suffix=".log",
    mimetype="text/plain",
    incluster_endpoint=minio_endpoint_incluster,
)
rip_done = MongoMetadataRepository(mongo, "rip_done")
rip_raw_output = S3BucketRepository(
    minio,
    minio_bucket,
    "rip_raw_output/",
    suffix=".tar.gz",
    mimetype="application/gzip",
    incluster_endpoint=minio_endpoint_incluster,
)
rip_exploits_data = S3BucketRepository(
    minio,
    minio_bucket,
    "rip_exploits/",
    suffix=".py",
    mimetype="text/plain",
    incluster_endpoint=minio_endpoint_incluster,
)
rip_exploits = MongoMetadataRepository(mongo, "rip_exploits")

crashes = MongoMetadataRepository(mongo, "crashes")
crashes_data = S3BucketRepository(
    minio, minio_bucket, "crashes_data/", incluster_endpoint=minio_endpoint_incluster
)
tmincrashes = MongoMetadataRepository(mongo, "tmincrashes")
tmincrashes_data = S3BucketRepository(
    minio, minio_bucket, "tmincrashes_data/", incluster_endpoint=minio_endpoint_incluster
)
exploits = S3BucketRepository(
    minio, minio_bucket, "exploits/", ".py", incluster_endpoint=minio_endpoint_incluster
)

postauthcrashes = MongoMetadataRepository(mongo, "postauthcrashes")
postauthcrashes_data = S3BucketRepository(
    minio, minio_bucket, "postauthcrashes_data/", incluster_endpoint=minio_endpoint_incluster
)
postauthexploits = S3BucketRepository(
    minio, minio_bucket, "postauthexploits/", ".py", incluster_endpoint=minio_endpoint_incluster
)

async def getter(info):
    return info.get("sample", "")


crash_to_sample = crashes.map(getter)
postauthcrash_to_sample = postauthcrashes.map(getter)

rex_logs = S3BucketRepository(
    minio,
    minio_bucket,
    "rex_logs/",
    suffix=".log",
    mimetype="text/plain",
    incluster_endpoint=minio_endpoint_incluster,
)
rex_done = MongoMetadataRepository(mongo, "rex_done")
postauthrex_logs = S3BucketRepository(
    minio,
    minio_bucket,
    "postauthrex_logs/",
    suffix=".log",
    mimetype="text/plain",
    incluster_endpoint=minio_endpoint_incluster,
)
postauthrex_done = MongoMetadataRepository(mongo, "postauthrex_done")
