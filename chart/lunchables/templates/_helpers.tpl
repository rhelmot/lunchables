{{/*
Expand the name of the chart.
*/}}
{{- define "lunchables.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "lunchables.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "lunchables.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "lunchables.labels" -}}
helm.sh/chart: {{ include "lunchables.chart" . }}
{{ include "lunchables.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "lunchables.selectorLabels" -}}
app.kubernetes.io/name: {{ include "lunchables.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
MY STUFF BEGINS HERE
*/}}
{{- define "lunchables.rwx-pvc" -}}
{{- if .Values.rwx.provision -}}
    {{ .Release.Name }}-rwx
{{- else -}}
    {{ .Values.rwx.existingPvc }}
{{- end }}
{{- end }}

{{- define "lunchables.rwx-path" -}}
{{- if .Values.rwx.provision -}}
    /
{{- else -}}
    {{ .Values.rwx.existingPath }}
{{- end }}
{{- end }}

{{- define "lunchables.elasticsearch-svc" -}}
{{- .Release.Name }}-elasticsearch
{{- end }}

{{- define "lunchables.kibana-svc" -}}
{{- include "common.names.dependency.fullname" (dict "chartName" "kibana" "chartValues" .Values.elasticsearch.kibana "context" $) }}
{{- end }}

{{- define "lunchables.elasticsearch-endpoint" -}}
{{- if .Values.elasticsearch.enabled -}}
    {{include "lunchables.elasticsearch-svc" . }}.{{ .Release.Namespace }}.svc.{{ .Values.global.clusterDomain }}:9200
{{- else -}}
    {{- .Values.elasticsearch.existingEndpoint -}}
{{- end }}
{{- end }}

{{- define "lunchables.minio-svc" -}}
{{- include "common.names.dependency.fullname" (dict "chartName" "minio" "chartValues" .Values.minio "context" $) }}
{{- end }}

{{- define "lunchables.minio-endpoint" -}}
{{- if .Values.minio.enabled -}}
    {{ include "lunchables.minio-svc" . }}.{{ .Release.Namespace }}.svc.{{ .Values.global.clusterDomain }}:9000
{{- else -}}
    {{- .Values.minio.existingEndpoint -}}
{{- end }}
{{- end }}

{{- define "lunchables.minio-username" -}}
{{- if .Values.minio.enabled -}}
    {{- .Values.minio.auth.rootUser -}}
{{- else -}}
    {{- .Values.minio.existingUsername -}}
{{- end }}
{{- end }}

{{- define "lunchables.minio-password" -}}
{{- if .Values.minio.enabled -}}
    {{- .Values.minio.auth.rootPassword -}}
{{- else -}}
    {{- .Values.minio.existingPassword -}}
{{- end }}
{{- end }}

{{- define "lunchables.mongo-svc" -}}
{{- include "common.names.dependency.fullname" (dict "chartName" "mongodb" "chartValues" .Values.mongodb "context" $) }}
{{- end }}

{{- define "lunchables.mongo-url" -}}
{{- if .Values.mongodb.enabled -}}
    mongodb://{{ index .Values.mongodb.auth.usernames 0 }}:{{ index .Values.mongodb.auth.passwords 0 }}@{{ include "lunchables.mongo-svc" . }}.{{ .Release.Namespace }}.svc.{{ .Values.global.clusterDomain }}:27017/{{ index .Values.mongodb.auth.databases 0 }}
{{- else -}}
    {{- .Values.mongodb.existingUrl -}}
{{- end }}
{{- end }}

{{- define "lunchables.mongo-url-localhost" -}}
mongodb://{{ index .Values.mongodb.auth.usernames 0 }}:{{ index .Values.mongodb.auth.passwords 0 }}@localhost:27017/{{ index .Values.mongodb.auth.databases 0 }}
{{- end }}

{{- define "lunchables.mongo-database" -}}
{{- if .Values.mongodb.enabled -}}
    {{- index .Values.mongodb.auth.databases 0 -}}
{{- else -}}
    {{- .Values.mongodb.existingDatabase -}}
{{- end }}
{{- end }}

{{- define "lunchables.leader-image" -}}
{{ .Values.dockerRegistry.images.leader }}
{{- end }}

{{- define "lunchables.gh2fuzz-image" -}}
{{ .Values.dockerRegistry.images.gh2fuzz }}
{{- end }}

{{- define "lunchables.gh2fuzz_postauth-image" -}}
{{ .Values.dockerRegistry.images.gh2fuzz_postauth }}
{{- end }}

{{- define "lunchables.gh2routersploit-image" -}}
{{ .Values.dockerRegistry.images.gh2routersploit }}
{{- end }}

{{- define "lunchables.rip-image" -}}
{{ .Values.dockerRegistry.images.rip }}
{{- end }}

{{- define "lunchables.rex-image" -}}
{{ .Values.dockerRegistry.images.rex }}
{{- end }}

{{- define "lunchables.greenhouse-image" -}}
{{ .Values.dockerRegistry.images.greenhouse }}
{{- end }}

{{- define "lunchables.localenv" -}}
export FUZZER_TIMEOUT_HOURS={{ .Values.fuzzer.timeoutHours }}
export MONGO_SECRET={{ .Release.Name }}-mongo
export MONGO_URL={{ include "lunchables.mongo-url-localhost" . }}
export MONGO_URL_INCLUSTER={{ include "lunchables.mongo-url" . }}
export MONGO_DATABASE={{ include "lunchables.mongo-database" . }}
export BUCKET_USERNAME={{ include "lunchables.minio-username" . }}
export BUCKET_ENDPOINT=localhost:9000
export BUCKET_ENDPOINT_INCLUSTER={{ include "lunchables.minio-endpoint" . }}
export BUCKET_SECRET={{ .Release.Name }}-minio
export BUCKET_PASSWORD={{ include "lunchables.minio-password" . }}
export BUCKET_BUCKET={{ .Values.minio.bucketName }}
export ELASTIC_SECRET={{ .Release.Name }}-elastic
export ELASTIC_LOGS_ENDPOINT=localhost:9200
export ELASTIC_LOGS_INDEX={{ .Values.elasticsearch.indexName }}
export RWX_PVC={{ include "lunchables.rwx-pvc" . }}
export RWX_PATH={{ include "lunchables.rwx-path" . }}
export KUBE_SECRET={{ .Release.Name }}-kube
export KUBE_NAMESPACE={{ .Release.Namespace }}
export KUBE_RELEASE_NAME={{ .Release.Name }}
export KUBE_MEM_QUOTA={{ .Values.pipelineResources.mem }}
export KUBE_CPU_QUOTA={{ .Values.pipelineResources.cpu }}
export IMAGE_FUZZING={{ .Values.dockerRegistry.images.fuzzing }}
export IMAGE_LEADER={{ include "lunchables.leader-image" . }}
export IMAGE_REX={{ include "lunchables.rex-image" . }}
export IMAGE_GREENHOUSE={{ include "lunchables.greenhouse-image" . }}
export IMAGE_GH2FUZZ={{ include "lunchables.gh2fuzz-image" . }}
export IMAGE_GH2FUZZ_POSTAUTH={{ include "lunchables.gh2fuzz_postauth-image" . }}
export IMAGE_RIP={{ include "lunchables.rip-image" . }}
export IMAGE_GH2ROUTERSPLOIT={{ include "lunchables.gh2routersploit-image" . }}
export DOCKER_PULL_SECRET={{ .Release.Name }}-docker
export IMAGE_PULL_POLICY={{ .Values.dockerRegistry.imagePullPolicy }}
export DOCKER_REGISTRY={{ .Values.dockerRegistry.domain }}
{{- range $index, $mapping := .Values.priorities }}
export PRIORITY_{{ $index }}={{ $mapping | toJson | quote }}
{{- end }}
{{- end }}

{{- define "lunchables.localfwd" -}}
#!/bin/bash
{{ if .Values.elasticsearch.enabled -}}
kubectl port-forward -n {{ .Release.Namespace }} svc/{{ include "lunchables.elasticsearch-svc" . }} 9200 &
{{- end }}
{{- if .Values.minio.enabled }}
kubectl port-forward -n {{ .Release.Namespace }} svc/{{ include "lunchables.minio-svc" . }} 9000 &
{{- end }}
{{- if .Values.mongodb.enabled }}
kubectl port-forward -n {{ .Release.Namespace }} svc/{{ include "lunchables.mongo-svc" . }} 27017 &
{{- end }}
{{- if .Values.global.kibanaEnabled }}
kubectl port-forward -n {{ .Release.Namespace }} svc/{{ include "lunchables.kibana-svc" . }} 5601 &
{{- end }}
trap 'kill -INT $(jobs -p)' INT
wait
{{- end }}
