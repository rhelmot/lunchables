# syntax=docker/dockerfile:1.4
# docker buildx build -t docker.shellphish.net/haccs/leader .

# the commented lines are used to build pydatatask locally along with the leader
# in this case the docker invocation is:
# docker buildx build --build-context pydatatask=$HOME/proj/python/pydatatask -t docker.shellphish.net/haccs/leader .

#from alpine as pydatatask-1
#run apk add curl tar
#run curl https://codeload.github.com/rhelmot/pydatatask/tar.gz/refs/heads/main | tar -xz
#
#from scratch as pydatatask
#copy --from=pydatatask-1 /pydatatask-main /

from alpine

workdir /root
run apk add python3 py3-pip py3-psutil
add requirements.txt /root/requirements.txt
#run --mount=from=pydatatask,target=/run/pydatatask,rw pip install --no-cache-dir /run/pydatatask -r /root/requirements.txt
run pip install --no-cache-dir -r /root/requirements.txt
add leader.py /root/leader.py
add yaml /root/yaml
add classes.py /root/classes.py
add creds.py /root/creds.py
add repos.py /root/repos.py
entrypoint ["python3", "leader.py"]
cmd ["update"]
