FROM atomicguy/blender280

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
RUN curl -L https://github.com/animate1978/MB-Lab/archive/1_7_7.zip -o /tmp/manuelbastionilab.zip

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