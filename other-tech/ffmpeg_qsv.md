# 为FFMPEG添加Intel QSV支持

## 简介

使用CPU转码的速度过于慢，在使用12核心的i7-10710U CPU全力转码也只有75fps的情况下，使用自带的Mesa Intel® UHD Graphics (CML GT2)进行转码在CPU占用率只有1/3的情况下，就可以达到400+fps的转码速度，速度提升了6倍。

但是直接使用`apt-get`安装的ffmpeg是不带QSV支持的，因为QSV并不是开源的，所以只有自己编译了。

如果完全按照[Intel® Quick Sync Video Installation](https://www.intel.com/content/www/us/en/architecture-and-technology/quick-sync-video/quick-sync-video-installation.html)的指示安装，恐怕是要过错年的。文档的格式排版辣眼睛不说，而且连术语都变了，文档让你安装的MediaServerStudio，早已经变成了MediaSDK。

## 安装Media SDK

首先到Github上下载MediaSDK：https://github.com/Intel-Media-SDK/MediaSDK/releases

当然按照Intel的尿性，下载的位置可能有变化，找不到的时候就参考一下官方页面：[Intel® Media SDK](https://www.intel.com/content/www/us/en/developer/tools/media-sdk/overview.html)。

随后解开压缩包，并且执行其中的安装脚本：

```bash
tar -xzvf MediaStack.tar.gz
cd MediaStack
chmod +x install_media.sh
sudo ./install_media.sh
```

这第一步就算完了。

## 编译FFMPEG

Intel文档里的这一部分不能说完全正确吧，只能说错漏百出。这里参考ffmpeg的官方的Wiki比较好。

首先安装需要的包：

```bash
sudo apt-get update -qq && sudo apt-get -y install \
  autoconf \
  automake \
  build-essential \
  cmake \
  libass-dev \
  libfreetype6-dev \
  libgnutls28-dev \
  libmp3lame-dev \
  libsdl2-dev \
  libtool \
  libva-dev \
  libvdpau-dev \
  libvorbis-dev \
  libxcb1-dev \
  libxcb-shm0-dev \
  libxcb-xfixes0-dev \
  meson \
  ninja-build \
  pkg-config \
  texinfo \
  wget \
  yasm \
  zlib1g-dev \
  libunistring-dev \
  libaom-dev \
  git-core libdav1d-dev
```

官网文档要求安装这些包，但是我的Ubuntu 20.04找不到`libdav1d-dev`所以干脆不装了，不影响QSV的使用，git-core也可以不用安装，不过我的机器上已经安装了git了。

之后下载源代码并且生成配置：

```bash
wget -O ffmpeg-snapshot.tar.bz2 https://ffmpeg.org/releases/ffmpeg-snapshot.tar.bz2
tar xjvf ffmpeg-snapshot.tar.bz2
cd ffmpeg
./configure --enable-libmfx --enable-nonfree | tee config.out
```

注意，由于我们可能不止使用qsv的ffmpeg，所以一个比较实用的命令会是：

```
./configure --enable-libmfx --enable-nonfree --enable-gpl --enable-libx264 --enable-libx265 --enable-libvpx --enable-libopus --enable-libsvtav1 | tee config.out
```

这个时候可能会提示：`ERROR: libmfx not found`。

参考[这个ISSUE](https://github.com/Intel-Media-SDK/MediaSDK/issues/1822)

只需要`export PKG_CONFIG_PATH=/opt/intel/mediasdk/lib/pkgconfig/`就可以了。

实际情况是，我的电脑是64位，所以应该是：`export PKG_CONFIG_PATH=/opt/intel/mediasdk/lib64/pkgconfig`。

最后直接make就行：

```bash
make -j 12
```

编译完看一眼支持的codec是不是正确：

```bash
./ffmpeg -codecs|grep qsv
```

正确的话应该输出类似：

```
ffmpeg version N-105268-g8b9ef5a516 Copyright (c) 2000-2022 the FFmpeg developers
  built with gcc 9 (Ubuntu 9.3.0-17ubuntu1~20.04)
  configuration: --enable-libmfx --enable-nonfree
  libavutil      57. 18.100 / 57. 18.100
  libavcodec     59. 20.100 / 59. 20.100
  libavformat    59. 17.100 / 59. 17.100
  libavdevice    59.  5.100 / 59.  5.100
  libavfilter     8. 25.100 /  8. 25.100
  libswscale      6.  5.100 /  6.  5.100
  libswresample   4.  4.100 /  4.  4.100
 D.V.L. av1                  Alliance for Open Media AV1 (decoders: av1 av1_qsv )
 DEV.LS h264                 H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10 (decoders: h264 h264_v4l2m2m h264_qsv ) (encoders: h264_qsv h264_v4l2m2m h264_vaapi )
 DEV.L. hevc                 H.265 / HEVC (High Efficiency Video Coding) (decoders: hevc hevc_qsv hevc_v4l2m2m ) (encoders: hevc_qsv hevc_v4l2m2m hevc_vaapi )
 DEVIL. mjpeg                Motion JPEG (decoders: mjpeg mjpeg_qsv ) (encoders: mjpeg mjpeg_qsv mjpeg_vaapi )
 DEV.L. mpeg2video           MPEG-2 video (decoders: mpeg2video mpegvideo mpeg2_v4l2m2m mpeg2_qsv ) (encoders: mpeg2video mpeg2_qsv mpeg2_vaapi )
 D.V.L. vc1                  SMPTE VC-1 (decoders: vc1 vc1_qsv vc1_v4l2m2m )
 DEV.L. vp8                  On2 VP8 (decoders: vp8 vp8_v4l2m2m vp8_qsv ) (encoders: vp8_v4l2m2m vp8_vaapi )
 DEV.L. vp9                  Google VP9 (decoders: vp9 vp9_v4l2m2m vp9_qsv ) (encoders: vp9_vaapi vp9_qsv )
```

## 测试

编译出来的ffmpeg就可以直接用了，这时我测试的指令：

```bash
./ffmpeg -i input.mp4 -init_hw_device qsv=hw -filter_hw_device hw -vf hwupload=extra_hw_frames=64,format=qsv -c:v h264_qsv -maxrate 5M -movflags +faststart output.mp4
```

在实际测试的过程中，一些选项是不能用的，比如`-pix_fmt yuv420p -crf 23`这一类的，去掉就可以。

偶尔会遇到像素格式不对的问题，需要设置如此设置 `-vf hwupload=extra_hw_frames=64,scale_qsv=format=nv12`。
但是在实际测试中，这样的转码速度会下降，不知道是不是像素格式引起的。

## 参考资料

* [FFMPEG wiki Hardware/QuickSync](https://trac.ffmpeg.org/wiki/Hardware/QuickSync)
* [Compile FFmpeg for Ubuntu, Debian, or Mint](https://trac.ffmpeg.org/wiki/CompilationGuide/Ubuntu)
* [英特尔® 快速视频同步 (Quick Sync Video) 技术-英特尔® 官网](https://www.intel.cn/content/www/cn/zh/architecture-and-technology/quick-sync-video/quick-sync-video-general.html)
* [Intel® Quick Sync Video Installation](https://www.intel.com/content/www/us/en/architecture-and-technology/quick-sync-video/quick-sync-video-installation.html)
* [Intel® Media SDK](https://www.intel.com/content/www/us/en/developer/tools/media-sdk/overview.html)
