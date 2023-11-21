INSTALL="lunchables"
NAMESPACE="rhelmot"

ROOTDIR="$(realpath "$(dirname "$(realpath "$0")")"/..)"
CHART="$ROOTDIR/chart/lunchables"
helm dependency build "$CHART"
helm upgrade "$INSTALL" "$CHART" --install --namespace "$NAMESPACE" -f "$ROOTDIR/deploy/connections.yaml" -f "$ROOTDIR/deploy/resources.yaml" -f "$ROOTDIR/deploy/images.yaml" -f "$ROOTDIR/deploy/secrets.yaml" "$@"
