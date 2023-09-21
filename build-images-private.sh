#!/bin/sh -e

REGISTRY="${1-docker.shellphish.net}"
PREFIX="${2-lunchables}"
TAG="${3-latest}"
if [ -z "$REGISTRY" ]; then
	echo "Usage: $0 registry [prefix] [tag]"
	exit 1
fi

make -C ./gh2fuzz/fuzz_bins_src
cd greenhouse
docker pull ubuntu:20.04
docker save -o ubuntu.tar ubuntu:20.04
cd -

dockerbuild() {
	IMAGE="$REGISTRY/$PREFIX/$1:$TAG"
	shift
	docker buildx build --build-arg BUILDKIT_INLINE_CACHE=1 -t "$IMAGE" --cache-from "$IMAGE" "$@"
	if [ -z "$NO_PUSH" ]; then
		docker push $IMAGE
	fi
}
dockerbuild leader leader
dockerbuild gh2fuzz gh2fuzz
dockerbuild rex T-Rex
dockerbuild greenhouse greenhouse
dockerbuild gh2routersploit routersploit
dockerbuild rip haccs-rip -f haccs-rip/dockervm/Dockerfile
