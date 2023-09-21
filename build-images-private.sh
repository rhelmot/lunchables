#!/bin/sh -e

BASEDIR="$(dirname $(realpath $0))"
REGISTRY="${1-docker.shellphish.net}"
PREFIX="${2-lunchables}"
TAG="${3-$(date +%Y-%m-%d-%H-%M-%S-%z)}"
if [ -z "$REGISTRY" ]; then
	echo "Usage: $0 registry [prefix] [tag]"
	exit 1
fi

cd greenhouse
docker pull ubuntu:20.04
docker save -o ubuntu.tar ubuntu:20.04
cd -

dockerbuild() {
	IMAGE="$REGISTRY/$PREFIX/$1:$TAG"
	CACHE="$REGISTRY/$PREFIX/$1-cache:latest"
	if [ -z "$NO_PUSH" ]; then
		PUSH="--push"
	fi

	shift
	docker buildx build $PUSH --cache-to "type=registry,ref=$CACHE" --cache-from "type=registry,ref=$CACHE" -t "$IMAGE" "$@"
}
dockerbuild leader leader
dockerbuild gh2fuzz gh2fuzz
dockerbuild rex T-Rex
dockerbuild greenhouse greenhouse
dockerbuild gh2routersploit routersploit
dockerbuild rip haccs-rip -f haccs-rip/dockervm/Dockerfile

cat >$BASEDIR/deploy/images.yaml <<EOF
dockerRegistry:
  images:
    leader: "$REGISTRY/$PREFIX/leader:$TAG"
    rex: "$REGISTRY/$PREFIX/rex:$TAG"
    gh2fuzz: "$REGISTRY/$PREFIX/gh2fuzz:$TAG"
    greenhouse: "$REGISTRY/$PREFIX/greenhouse:$TAG"
    gh2routersploit: "$REGISTRY/$PREFIX/gh2routersploit:$TAG"
    rip: "$REGISTRY/$PREFIX/rip:$TAG"
EOF

echo "Image configuration written to $BASEDIR/deploy/images.yaml"
