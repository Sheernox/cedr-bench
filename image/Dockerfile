# Edition 1 base only. The runner installs one agent in a separate local layer.
# Fixed linux/amd64 target; archive checksums are architecture-specific.
FROM --platform=linux/amd64 debian:12@sha256:268fb24c39bca92d326dd83ea3abebe4a3f7751c804ffef23bb6d857dd343ff8

# Signed, dated APT snapshots pin transitive dependencies as well as these
# explicit package versions. TLS verification is disabled ONLY for bootstrap:
# the minimal base has no CA store; APT still verifies Debian signatures/hashes.
RUN rm /etc/apt/sources.list.d/debian.sources && \
    printf 'deb [check-valid-until=no] https://snapshot.debian.org/archive/debian/20261111T000000Z bookworm main\ndeb [check-valid-until=no] https://snapshot.debian.org/archive/debian-security/20261111T000000Z bookworm-security main\n' > /etc/apt/sources.list && \
    apt-get -o Acquire::https::Verify-Peer=false update -qq && \
    apt-get -o Acquire::https::Verify-Peer=false install -y --no-install-recommends \
      ca-certificates=20250419~deb12u2 \
      python3=3.11.2-1+b1 python3-venv=3.11.2-1+b1 \
      git=1:2.39.5-0+deb12u3 curl=7.88.1-10+deb12u15 xz-utils=5.4.1-1+deb12u2 \
      fontconfig=2.14.1-4 libcups2=2.4.2-3+deb12u9 libnss3=2:3.87.1-1+deb12u4 \
      libatk-bridge2.0-0=2.46.0-5 libatspi2.0-0=2.46.0-5 \
      libdrm2=2.4.114-1+b1 libxkbcommon0=1.5.0-1 libxcomposite1=1:0.4.5-1 \
      libxdamage1=1:1.1.6-1 libxfixes3=1:6.0.0-2 libxrandr2=2:1.5.2-2+b1 \
      libgbm1=22.3.6-1+deb12u2 libasound2=1.2.8-1+b1 \
      libpango-1.0-0=1.50.12+ds-1 libcairo2=1.16.0-7 libatomic1=12.2.0-14+deb12u1 && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://nodejs.org/dist/v26.13.1/node-v26.13.1-linux-x64.tar.xz -o /tmp/node.tar.xz && \
    echo '5c063e46bab0fbc1c17cc445d7ff129cbdcd0471be6ed83b6ab864f8143bc864  /tmp/node.tar.xz' | sha256sum -c - && \
    tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 && rm /tmp/node.tar.xz

COPY image/requirements.txt /opt/bench/requirements.txt
RUN python3 -m venv /opt/bench/venv && \
    /opt/bench/venv/bin/pip install --disable-pip-version-check --no-cache-dir \
      --only-binary=:all: --require-hashes -r /opt/bench/requirements.txt
COPY image/assets.py /opt/bench/assets.py
COPY image/licenses/ /usr/share/licenses/bench-fonts/
RUN python3 /opt/bench/assets.py && fc-cache -f && \
    dpkg-query -W > /opt/bench/debian-packages.txt && \
    /opt/chromium/chrome-linux/chrome --version && \
    node --version && python3 --version

ENV PATH="/opt/bench/venv/bin:${PATH}" \
    HOME=/home/bench LANG=C.UTF-8 TZ=UTC \
    PYTHONDONTWRITEBYTECODE=1 \
    BENCH_CHROMIUM_EXECUTABLE=/opt/chromium/chrome-linux/chrome \
    BENCH_CHROMIUM_NO_SANDBOX=1
RUN groupadd --gid 1000 bench && useradd --uid 1000 --gid 1000 --create-home --home-dir /home/bench bench && \
    mkdir /workspace && chown bench:bench /workspace
USER bench
WORKDIR /workspace
CMD ["/bin/bash"]
