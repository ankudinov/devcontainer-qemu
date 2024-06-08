FROM mcr.microsoft.com/vscode/devcontainers/base:ubuntu

ARG CLAB_VERSION

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    qemu-kvm \
    libvirt-daemon \
    python3 \
    python3-pip

# add ceos-lab image is _ARTOKEN is not empty
# RUN if [ ! -z ${_ARTOKEN} ]; \
#     then \
#     ARTOKEN=$(echo -n "${_ARTOKEN}" | base64) \
#     && ARSESSION=$(curl -X "POST" "https://www.arista.com/custom_data/api/cvp/getSessionCode/" -H 'Content-Type: application/json'   -d "{\"accessToken\": \"$ARTOKEN\"}" | sed -n 's|.*"session_code":"\([^"]*\)".*|\1|p') \
#     && FILE_PATH=${_AR_FILE_PATH} \
#     && DOWNLOAD_URL=$(curl -X "POST" "https://www.arista.com/custom_data/api/cvp/getDownloadLink/" -H 'Content-Type: application/json' -d "{\"sessionCode\": \"$ARSESSION\", \"filePath\": \"$FILE_PATH\"}" | sed -n 's|.*"url":"\([^"]*\)".*|\1|p') \
#     && mkdir -p /home/vscode/tmp \
#     && curl "$DOWNLOAD_URL" --output /home/vscode/tmp/cvp-kvm.tgz \
#     ; fi

# copy postCreate script
COPY ./postCreate.sh /bin/postCreate.sh
RUN chmod +x /bin/postCreate.sh

# install the latest yamllint and eos-downloader
RUN bash -c "$(curl -sL https://get.containerlab.dev)" -- -v ${CLAB_VERSION} \
    && pip install --user "eos-downloader>=0.10.1"
