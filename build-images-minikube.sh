#!/bin/bash -e

eval $(minikube docker-env)

NO_PUSH=1 ./build-images-private.sh minikube haccs latest

cat <<EOF
All done!
Use the following configuration in your config.yaml:

dockerRegistry:
  domain: unused
  username: unused
  password: unused
  email: unused

  imagePullPolicy: Never

  images:
    leader: minikube/haccs/leader:latest
    rex: minikube/com/haccs/rex:latest
    gh2fuzz: minikube/haccs/gh2fuzz:latest
    greenhouse: minikube/haccs/greenhouse:latest
    gh2routersploit: minikube/haccs/gh2routersploit:latest
    rip: minikube/haccs/rip:latest
EOF
