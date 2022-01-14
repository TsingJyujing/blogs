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
  git-core \
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
  libdav1d-dev
```

官网文档要求安装这些包，但是我的Ubuntu 20.04找不到`libdav1d-dev`所以干脆不装了，不影响QSV的使用。

之后下载源代码并且生成配置：

```bash
wget -O ffmpeg-snapshot.tar.bz2 https://ffmpeg.org/releases/ffmpeg-snapshot.tar.bz2
tar xjvf ffmpeg-snapshot.tar.bz2
cd ffmpeg
./configure --enable-libmfx --enable-nonfree | tee config.out
```

这个时候可能会提示：`ERROR: libmfx not found`。

参考这个ISSUE：https://github.com/Intel-Media-SDK/MediaSDK/issues/1822

只需要`export PKG_CONFIG_PATH=/opt/intel/mediasdk/lib/pkgconfig/`就可以了。

实际情况是，我的电脑是64位，所以应该是：`export PKG_CONFIG_PATH=/opt/intel/mediasdk/lib64/pkgconfig`。

最后直接make就行：

```bash
make -j 12
```


## 测试

编译出来的ffmpeg就可以直接用了，这时我测试的指令：

```bash
./ffmpeg -i input.mp4 -init_hw_device qsv=hw -filter_hw_device hw -vf hwupload=extra_hw_frames=64,format=qsv -c:v h264_qsv -maxrate 5M -movflags +faststart output.mp4
```

在实际测试的过程中，一些选项是不能用的，比如`-pix_fmt yuv420p -crf 23`这一类的，去掉就可以。


## 参考资料

- [FFMPEG wiki Hardware/QuickSync](https://trac.ffmpeg.org/wiki/Hardware/QuickSync)
- [Compile FFmpeg for Ubuntu, Debian, or Mint](https://trac.ffmpeg.org/wiki/CompilationGuide/Ubuntu)
- [英特尔® 快速视频同步 (Quick Sync Video) 技术-英特尔® 官网](https://www.intel.cn/content/www/cn/zh/architecture-and-technology/quick-sync-video/quick-sync-video-general.html)
- [Intel® Quick Sync Video Installation](https://www.intel.com/content/www/us/en/architecture-and-technology/quick-sync-video/quick-sync-video-installation.html)
- [Intel® Media SDK](https://www.intel.com/content/www/us/en/developer/tools/media-sdk/overview.html)