# 视频压制技术笔记

## 不同视频网站的不同标准

- [Youtube](https://support.google.com/youtube/answer/1722171)


## Youtube

- Progressive scan (no interlacing)
    - Default: https://blog.p2hp.com/archives/7328
- High Profile
- 2 consecutive B frames
    - https://www.reddit.com/r/ffmpeg/comments/g708bz/show_the_consecutive_bframes_before_encoding/
    - https://sites.google.com/site/linuxencoding/x264-ffmpeg-mapping
- Closed GOP. GOP of half the frame rate.
    - Default: https://streaminglearningcenter.com/blogs/open-and-closed-gops-all-you-need-to-know.html
- CABAC
    - Default: https://sites.google.com/site/linuxencoding/x264-ffmpeg-mapping
- Variable bitrate. No bitrate limit required, though we offer recommended bit rates below for reference
    - Default
- Chroma subsampling: 4:2:0
    - https://trac.ffmpeg.org/wiki/Chroma%20Subsampling


Test commands:

```bash
ffmpeg -hwaccel_output_format qsv -hwaccel qsv -i input.mp4 -c:v h264_qsv -bf 2 -b:v 6M -maxrate 24M -global_quality 25 -look_ahead 1 -pix_fmt yuv420p output.mp4
ffmpeg -i input.mp4 -c:v libx264 -bf 2 -b:v 7M -maxrate 24M -crf 30 -movflags +faststart -pix_fmt yuv420p output.mp4
# Youtube compress
ffmpeg -i input.mp4 -vf yadif,format=yuv422p -force_key_frames 'expr:gte(t,n_forced/2)' -c:v libx264 -crf ${CRF_VALUE} -maxrate 12M -bf 2 -c:a aac -ac 2 -ar 44100 -use_editlist 0 -movflags +faststart output.mp4
```

## Bilibili

## References

- https://trac.ffmpeg.org/wiki/Encode/H.264
