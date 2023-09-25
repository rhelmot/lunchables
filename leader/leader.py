#!/usr/bin/env python3
from typing import List
from pathlib import Path
from datetime import timedelta
import os
import asyncio
import argparse
import aiofiles
import io
import tarfile
import logging
import json

from pydatatask import (
    KubeTask,
    KubeFunctionTask,
    main,
    Pipeline,
    BlobRepository,
    MetadataRepository,
    FileRepository,
    YamlMetadataFileRepository,
    RelatedItemRepository,
)
from creds import (
    podman,
    kube_quota,
    config_root,
    image_greenhouse,
    image_pull_secret,
    rwx_pvc,
    image_gh2fuzz,
    image_gh2fuzz_postauth,
    image_gh2routersploit,
    image_rip,
    fuzzer_timeout,
    image_rex,
    idgen,
    bucket_secret,
    mongo_secret,
    session,
    incluster,
    shared_root,
    shared_suffix,
    get_priority,
    image_pull_policy,
)
from repos import (
    greenhouse_logs,
    greenhouse_done,
    greenhouse_collect_logs,
    greenhouse_collect_kube_done,
    greenhouse_collect_func_done,
    fuzz_logs,
    fuzz_done,
    rex_logs,
    rex_done,
    postauthfuzz_logs,
    postauthfuzz_done,
    targets,
    greenhouse_results,
    greenhouse_meta,
    greenhouse_success,
    greenhouse_complete,
    crashes,
    crashes_data,
    tmincrashes,
    tmincrashes_data,
    crash_to_sample,
    exploits,
    postauthcrashes,
    postauthcrashes_data,
    routersploit_logs,
    routersploit_done,
    routersploit_results,
    rip_raw_output,
    rip_logs,
    rip_done,
    rip_exploits,
    rip_exploits_data,
)

log = logging.getLogger("leader")
log.setLevel("DEBUG")

greenhouse = KubeTask(
    "greenhouse",
    podman,
    kube_quota,
    config_root / "greenhouse.yaml",
    logs=greenhouse_logs,
    done=greenhouse_done,
)
greenhouse.link("target", targets, is_input=True)
greenhouse.link("greenhouse_result", greenhouse_results, is_output=True)
greenhouse.env["self_image"] = image_greenhouse
greenhouse.env["image_pull_secret"] = image_pull_secret
greenhouse.env["rwx_pvc"] = rwx_pvc
greenhouse.env["bucket_secret"] = bucket_secret
greenhouse.env["image_pull_policy"] = image_pull_policy


@KubeFunctionTask(
    "greenhouse_collect_meta",
    podman,
    kube_quota,
    config_root / "function.yaml",
    logs=greenhouse_collect_logs,
    kube_done=greenhouse_collect_kube_done,
    func_done=greenhouse_collect_func_done,
)
async def greenhouse_collect_meta(job, greenhouse_results, greenhouse_meta):
    # ughhhhhhhhhhhhhhhhhhh
    try:
        async with await greenhouse_results.open(job, "rb") as fp:
            data = io.BytesIO(await fp.read())
    except Exception:
        log.exception("TODO FIXME who am I?")
        config = {}
    else:
        tar = tarfile.open(fileobj=data, mode="r")
        while True:
            info = tar.next()
            if info is None:
                config = {}
                break

            if (
                info.name.endswith("/config.json")
                and "/minimal/" not in info.name
                and "/debug/" not in info.name
            ):
                config = json.load(tar.extractfile(info))
                break

    try:
        old_config = await greenhouse_meta.info(job)
        attempts = old_config["attempts"] + 1
    except (KeyError, TypeError):
        attempts = 1

    config["attempts"] = attempts

    try:
        success = config["result"] == "SUCCESS"
    except (KeyError, TypeError):
        success = False

    if attempts < 3 and not success:
        log.info("Greenhouse failed on %s; retrying %d", job, attempts)
        await greenhouse_logs.delete(job)
        await greenhouse_done.delete(job)
        await greenhouse_results.delete(job)

    await greenhouse_meta.dump(job, config)


greenhouse_collect_meta.links["logs"].inhibits_start = False
greenhouse_collect_meta.links["done"].inhibits_start = False
greenhouse_collect_meta.links["func_done"].inhibits_start = False
greenhouse_collect_meta.link(
    "greenhouse_results", greenhouse_results, is_input=True, required_for_start=False
)
greenhouse_collect_meta.link(
    "greenhouse_meta", greenhouse_meta, is_output=True, inhibits_start=False
)
greenhouse_collect_meta.link(
    "greenhouse_success",
    greenhouse_success,
    is_output=True,
    inhibits_start=False,
    required_for_output=False,
)
greenhouse_collect_meta.env["env"] = os.environ
greenhouse_collect_meta.link(
    "greenhouse_complete", greenhouse_complete, is_output=True, inhibits_start=True
)
greenhouse_collect_meta.link(
    "greenhouse_done", greenhouse_done, required_for_start=True
)

fuzz = KubeTask(
    "fuzz",
    podman,
    kube_quota,
    config_root / "fuzz.yaml",
    logs=fuzz_logs,
    done=fuzz_done,
)
fuzz.link("target", targets, is_input=True)
fuzz.link("greenhouse_complete", greenhouse_complete, is_input=True)
fuzz.plug(greenhouse)
fuzz.link("crash", crashes, is_output=True)
fuzz.link("crash_data", crashes_data, is_output=True)
fuzz.link("tmincrash", tmincrashes, is_output=True)
fuzz.link("tmincrash_data", tmincrashes_data, is_output=True)
fuzz.env["self_image"] = image_gh2fuzz
fuzz.env["image_pull_secret"] = image_pull_secret
fuzz.env["fuzz_timeout"] = int(fuzzer_timeout.total_seconds())
fuzz.env["mongo_subcollection"] = crashes._subcollection
fuzz.env["mongo_subcollection_tmin"] = tmincrashes._subcollection
fuzz.env["mongo_secret"] = mongo_secret
fuzz.env["bucket_secret"] = bucket_secret
fuzz.env["rwx_pvc"] = rwx_pvc
fuzz.env["image_pull_policy"] = image_pull_policy

postauthfuzz = KubeTask(
    "postauthfuzz",
    podman,
    kube_quota,
    config_root / "fuzz.yaml",
    logs=postauthfuzz_logs,
    done=postauthfuzz_done,
)
postauthfuzz.link("target", targets, is_input=True)
postauthfuzz.link("greenhouse_complete", greenhouse_complete, is_input=True)
postauthfuzz.plug(greenhouse)
postauthfuzz.link("crash", postauthcrashes, is_output=True)
postauthfuzz.link("crash_data", postauthcrashes_data, is_output=True)
postauthfuzz.env["self_image"] = image_gh2fuzz_postauth
postauthfuzz.env["image_pull_secret"] = image_pull_secret
postauthfuzz.env["fuzz_timeout"] = int(fuzzer_timeout.total_seconds())
postauthfuzz.env["mongo_subcollection"] = postauthcrashes._subcollection
postauthfuzz.env["mongo_secret"] = mongo_secret
postauthfuzz.env["bucket_secret"] = bucket_secret
postauthfuzz.env["rwx_pvc"] = rwx_pvc

routersploit = KubeTask(
    "routersploit",
    podman,
    kube_quota,
    config_root / "routersploit.yaml",
    logs=routersploit_logs,
    done=routersploit_done,
)
routersploit.link("greenhouse_complete", greenhouse_complete, is_input=True)
routersploit.plug(greenhouse)
routersploit.link("routersploit_result", routersploit_results, is_output=True)  # TODO
routersploit.env["self_image"] = image_gh2routersploit
routersploit.env["image_pull_secret"] = image_pull_secret
routersploit.env["bucket_secret"] = bucket_secret
routersploit.env["image_pull_policy"] = image_pull_policy


rip = KubeTask(
    "rip",
    podman,
    kube_quota,
    config_root / "rip.yaml",
    logs=rip_logs,
    done=rip_done,
)
rip.plug(greenhouse)
rip.plug(routersploit)
rip.link("rip_raw", rip_raw_output, is_output=True)
rip.link("rip_exploit_data", rip_exploits_data, is_output=True)
rip.link("rip_exploit", rip_exploits, is_output=True)
rip.env["self_image"] = image_rip
rip.env["image_pull_secret"] = image_pull_secret
rip.env["bucket_secret"] = bucket_secret
rip.env["mongo_secret"] = mongo_secret
rip.env["mongo_subcollection"] = rip_exploits._subcollection
rip.env["image_pull_policy"] = image_pull_policy


rex = KubeTask(
    "rex",
    podman,
    kube_quota,
    config_root / "rex.yaml",
    logs=rex_logs,
    done=rex_done,
    timeout=timedelta(hours=1),
)

# do not block rex on fuzz completion
rex.link("target", RelatedItemRepository(targets, crash_to_sample), is_input=True)
rex.plug(fuzz, meta=False)
rex.plug(greenhouse, translator=crash_to_sample, meta=False)
rex.link("exploit", exploits, is_output=True)
rex.env["self_image"] = image_rex
rex.env["image_pull_secret"] = image_pull_secret
rex.env["bucket_secret"] = bucket_secret
rex.env["image_pull_policy"] = image_pull_policy

pipeline = Pipeline(
    [
        greenhouse,
        greenhouse_collect_meta,
        fuzz,
        postauthfuzz,
        rex,
        routersploit,
        rip,
    ],
    session,
    [kube_quota],
    get_priority,
)


def more_actions(subparsers: argparse._SubParsersAction):
    parser_input = subparsers.add_parser(
        "inject_input", help="Add a firmware blob to analyze"
    )
    parser_input.add_argument(
        "--basename",
        required=True,
        help="The filename of the firmware blob. For your reference.",
    )
    parser_input.add_argument(
        "--brand",
        required=True,
        help="The brand of the firmware blob. For your reference.",
    )
    parser_input.set_defaults(func=action_inject_input)

    parser_crash = subparsers.add_parser(
        "inject_crash", help="Manually inject a crash for crash analysis"
    )
    parser_crash.add_argument(
        "--sample",
        required=True,
        help="The job ID of the sample to which this crash applies",
    )
    parser_crash.add_argument(
        "--jam",
        action="store_true",
        help="Mark the corresponding fuzzing job as complete - this will prevent "
        "future fuzzing jobs from spinning up and also allow AEG jobs to "
        "start immediately",
    )
    parser_crash.set_defaults(func=action_inject_crash)

    if incluster:
        parser_localinstall = subparsers.add_parser("localinstall", help="Print an install script to get a local copy of the admin script")
        parser_localinstall.set_defaults(func=action_localinstall)

    if not incluster:
        parser_backup = subparsers.add_parser(
            "backup", help="Copy contents of repositories to a given folder"
        )
        parser_backup.add_argument("backup_dir", help="The directory to backup to")
        parser_backup.add_argument(
            "repos", nargs="+", help="The repositories to back up"
        )
        parser_backup.set_defaults(func=action_backup)


async def action_inject_input(pipeline: Pipeline, basename: str, brand: str):
    if not shared_root.is_dir():
        print(
            f"The leader is running in an environment without the firmware storage dir mounted ({shared_root}). Cannot inject inputs."
        )
        return
    new_ident = 0
    async for ident in targets:
        ident_int = int(ident)
        if ident_int >= new_ident:
            new_ident = ident_int + 1
    fid = str(new_ident)
    try:
        try:
            await aiofiles.os.mkdir(shared_root / brand)
        except FileExistsError:
            pass
        async with aiofiles.open(shared_root / brand / basename, "wb") as fp:
            while True:
                data = await aiofiles.stdin_bytes.read(1024 * 1024)
                if not data:
                    break
                await fp.write(data)
        await targets.dump(
            fid,
            {
                "filename": str(shared_suffix / brand / basename),
                "basename": basename,
                "brand": brand,
            },
        )
    except:
        try:
            await aiofiles.os.unlink(shared_root / brand / basename)
            await targets.delete(fid)
        except:
            pass
        raise
    else:
        print(fid)


async def action_inject_crash(pipeline: Pipeline, sample: str, jam: bool):
    cid = str(idgen.next_id())
    try:
        async with await crashes_data.open(cid, "wb") as fp:
            while True:
                data = await aiofiles.stdin_bytes.read(1024 * 1024)
                if not data:
                    break
                await fp.write(data)
        await crashes.dump(
            cid,
            {
                "filename": "fake",
                "sample": sample,
            },
        )
    except:
        await crashes.delete(cid)
        await crashes_data.delete(cid)
        raise
    else:
        print(cid)

    # TODO is jam needed anymore
    # if jam:
    #    await phase4_done.dump(sample, {"jam": True})
    #    await phase2_done.dump(sample, {"jam": True})
    #    async with await phase2_logs.open(sample, "wb"):
    #        pass


async def _repo_copy_blob(repo_src: BlobRepository, repo_dst: BlobRepository):
    async for ident in repo_src:
        async with await repo_src.open(ident, "rb") as fp_r, await repo_dst.open(
            ident, "wb"
        ) as fp_w:
            while True:
                data = await fp_r.read(1024 * 1024)
                if not data:
                    break
                await fp_w.write(data)


async def _repo_copy_meta(repo_src: MetadataRepository, repo_dst: MetadataRepository):
    for ident, data in (await repo_src.info_all()).items():
        await repo_dst.dump(ident, data)


async def action_backup(pipeline: Pipeline, backup_dir: str, repos: List[str]):
    backup_base = Path(backup_dir)
    jobs = []
    for repo_name in repos:
        repo_base = backup_base / repo_name
        task, repo_basename = repo_name.split(".")
        repo = pipeline.tasks[task].links[repo_basename].repo
        if isinstance(repo, BlobRepository):
            new_repo = FileRepository(repo_base)
            await new_repo.validate()
            jobs.append(_repo_copy_blob(repo, new_repo))
        elif isinstance(repo, MetadataRepository):
            new_repo = YamlMetadataFileRepository(repo_base)
            await new_repo.validate()
            jobs.append(_repo_copy_meta(repo, new_repo))
        else:
            print("Warning: cannot backup", repo)

    await asyncio.gather(*jobs)

async def action_localinstall(pipeline):
    with open('/mnt/localcfg/install', 'r') as fp:
        print(fp.read(), end='')

if __name__ == "__main__":
    result = main(pipeline, more_actions)
    exit(result)
