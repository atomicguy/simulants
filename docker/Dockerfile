FROM python:3.7-slim-stretch

# blender install
RUN apt-get update && \
	apt-get install -y \
		curl \
		bzip2 \
		libfreetype6 \
		libgl1-mesa-dev \
		libglu1-mesa \
		libxi6 \
		libxrender1 && \
	apt-get -y autoremove && \
	rm -rf /var/lib/apt/lists/*

ENV BLENDER_MAJOR 2.79
ENV BLENDER_VERSION 2.79b
ENV BLENDER_BZ2_URL https://mirror.clarkson.edu/blender/release/Blender$BLENDER_MAJOR/blender-$BLENDER_VERSION-linux-glibc219-x86_64.tar.bz2

RUN mkdir /usr/local/blender && \
	curl -SL "$BLENDER_BZ2_URL" -o blender.tar.bz2 && \
	tar -jxvf blender.tar.bz2 -C /usr/local/blender --strip-components=1 && \
	rm blender.tar.bz2

VOLUME /media

# install docker toolchain
COPY scripts/apt-install /usr/local/bin

# install dependencies
RUN pip install numpy scipy Pillow joblib codenamize

# Set directory variables
ARG SCRIPTDIR=/tmp/blend_scripts
RUN mkdir $SCRIPTDIR

# link blender to Path
ENV PATH="/usr/local/blender:${PATH}"

# copy needed files
COPY blend_scripts/ $SCRIPTDIR

# download and install MBLab
RUN curl -L https://github.com/NumesSanguis/FACSvatar/releases/download/v0.3.4-alpha-release/manuelbastionilab_161a.zip -o /tmp/manuelbastionilab.zip

RUN blender -b --python $SCRIPTDIR/install_lab.py

# configure ENV
ARG SQDT_ROOT=/usr/local/src/x/sqDet
ENV SQDT_ROOT /usr/local/src/x/sqDet

ARG DATASET_ROOT=/usr/local/share/datasets
ENV DATASET_ROOT $DATASET_ROOT

ARG TF_LOG_ROOT=/usr/local/share/models
ENV TF_LOG_ROOT $TF_LOG_ROOT

ENTRYPOINT ["/bin/sh", "-c"]
WORKDIR /usr/local/src/x