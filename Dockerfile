FROM node:12

RUN echo "registry=https://nexus.tsingjyujing.com/repository/npm/\nstrict-ssl=false" > /root/.npmrc

# Set environment
RUN npm install gitbook-cli -g && \
    gitbook install && \
    apt-get update && \
    apt-get install -y git && \
    apt-get clean

WORKDIR /build-book
COPY book.json ./book.json
RUN gitbook install

# Build book
COPY . .
RUN gitbook build

# Upload books to tsingjyujing.github.io/blog
ARG GITHUB_PRIVATE_KEY

RUN mkdir ~/.ssh && \
    cp ssh_config ~/.ssh/config && \
    echo "${GITHUB_PRIVATE_KEY}" > ~/.ssh/id_rsa_github && \
    chmod 600 ~/.ssh/id_rsa_github

RUN git clone git@github.com:TsingJyujing/tsingjyujing.github.io.git /upload-book && \
    mkdir -p /upload-book/blog && \
    rm -rf /upload-book/blog/* && \
    cp -r ./_book/* /upload-book/blog/

ARG DRONE_COMMIT

WORKDIR /upload-book
RUN git config --global user.email "nigel434@gmail.com" && \
    git config --global user.name "Blog Update Robot" && \
    git add * && \
    git commit -m "[ROBOT] Update blog ${DRONE_COMMIT}" && \
    git push