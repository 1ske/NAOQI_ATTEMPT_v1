# naoqisim: NAOqi 2.1.4 running inside a Webots controller, attached to the Mac's Webots
# over the extern-controller TCP link. NAOqi is x86-only, so this runs emulated on Apple Silicon.
FROM --platform=linux/amd64 ubuntu:22.04

ARG WEBOTS_VERSION=R2025a
# Last commit of cyberbotics/naoqisim (deprecated, 2021-11-15)
ARG NAOQISIM_COMMIT=f4c167c5a6727137a4446b636d88459857d37651
ARG SDK=simulator-sdk-2.1.4.1-linux64.tar.gz
ARG SDK_SHA256=074744b7919edd59d293390ebe35648817881e2a656cc036b42f563267024c25

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential ca-certificates curl bzip2 git make netcat-openbsd \
      libglib2.0-0 libdbus-1-3 libusb-0.1-4 \
    && rm -rf /var/lib/apt/lists/*

# Webots for Linux, only for libController and the controller Makefiles.
# Must be the same version as the Webots running on the Mac.
ENV WEBOTS_HOME=/opt/webots
RUN curl -fsSL https://github.com/cyberbotics/webots/releases/download/${WEBOTS_VERSION}/webots-${WEBOTS_VERSION}-x86-64.tar.bz2 \
      | tar xj -C /opt
ENV LD_LIBRARY_PATH=${WEBOTS_HOME}/lib/controller

RUN git clone https://github.com/cyberbotics/naoqisim /opt/naoqisim \
    && git -C /opt/naoqisim checkout ${NAOQISIM_COMMIT}
WORKDIR /opt/naoqisim

# Simulator SDK: use the vendored copy if present, else download it.
COPY vendor/ /tmp/vendor/
RUN if [ -f /tmp/vendor/${SDK} ]; then mv /tmp/vendor/${SDK} aldebaran/; \
    else curl -fsSL -o aldebaran/${SDK} https://cyberbotics.com/files/repository/dependencies/linux64/release/${SDK}; fi \
    && echo "${SDK_SHA256}  aldebaran/${SDK}" | sha256sum -c - \
    && make -C aldebaran \
    && rm -rf /tmp/vendor aldebaran/${SDK}

COPY patches/ /tmp/patches/
RUN for p in /tmp/patches/*.patch; do echo "applying $p"; git apply "$p"; done \
    && make -C controllers/naoqisim WEBOTS_HOME_PATH=${WEBOTS_HOME}

ENV WEBOTS_NAOSIM_PATH=/opt/naoqisim/aldebaran/simulator-sdk
ENV LD_LIBRARY_PATH=${WEBOTS_NAOSIM_PATH}/lib:${WEBOTS_HOME}/lib/controller
# Fail if naoqisim, hal or naoqi-bin can't resolve a library; only list what plugin modules miss.
RUN for f in controllers/naoqisim/naoqisim ${WEBOTS_NAOSIM_PATH}/bin/hal ${WEBOTS_NAOSIM_PATH}/bin/naoqi-bin; do \
         if ldd "$f" | grep "not found"; then echo "missing libraries for $f"; exit 1; fi; \
       done \
    && for f in ${WEBOTS_NAOSIM_PATH}/lib/naoqi/*.so; do \
         ldd "$f" | grep "not found" | sed "s|^|$(basename $f): |" || true; \
       done
# Clock anomaly logger for tools/trials.sh (NOTES.md "Emulation stalls")
COPY clockwatch.c /tmp/clockwatch.c
RUN mkdir -p /opt/tools && gcc -O2 -Wall -o /opt/tools/clockwatch /tmp/clockwatch.c && rm /tmp/clockwatch.c
COPY entrypoint.sh /entrypoint.sh
# NAOqi refuses to run as root
RUN useradd -m nao
USER nao
EXPOSE 9559
ENTRYPOINT ["/entrypoint.sh"]
