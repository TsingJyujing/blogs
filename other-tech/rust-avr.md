# 用Rust开发AVR单片机

这个是失败的例子

## 环境准备

安装Rust，这一部分参考：https://github.com/avr-rust/rust

```bash
# FROM https://www.rust-lang.org/tools/install
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Enable it:

source $HOME/.cargo/env

# Add AVR toolchain:
git clone https://github.com/avr-rust/rust.git --recursive
```

安装rust的时候一定记住不能选完全模式（complete）否则会导致之后旧版本无法安装。

整个项目这样clone下来大约3.8G……嗯……准备永久收藏了。

然后是build整个项目：

```bash
# Grab the avr-rust sources
git clone https://github.com/avr-rust/rust.git --recursive

# Create a directory to place built files in
mkdir build && cd build

# Generate Makefile using settings suitable for an experimental compiler
../rust/configure \
  --enable-debug \
  --disable-docs \
  --enable-llvm-assertions \
  --enable-debug-assertions \
  --enable-optimize \
  --enable-llvm-release-debuginfo \
  --experimental-targets=AVR \
  --prefix=/usr/local/avr-rust

# Build the compiler, install it to /usr/local/avr-rust
make
make install
```

make和make install这两步可能耗费数小时，需要十足的耐心。

就我的记录而言，编译的相当惨烈啊……

![](/img/2020-07-18-23-49-41.png)

最后安装就好了：

```bash
# Register the toolchain with rustup
# MAC
rustup toolchain link avr-toolchain /usr/local/avr-rust
# Linux
rustup toolchain link avr-toolchain $(realpath $(find . -name 'stage2'))

# Optionally enable the avr toolchain globally
rustup default avr-toolchain
```

这个时候切换旧版本：`rustup toolchain install 1.37.0`

然后准备安装xargo，也不能直接安装，需要clone源代码切换到0.3.17版本。

```bash
git clone https://github.com/japaric/xargo.git
git checkout tags/v0.3.17
cargo install --path ./ --locked
```

目前为止，仍然失败，暂时放弃。