# React-Script转Vite时引用路径的问题

最大的问题是Import Path的问题，正常情况下，如果我有这样的src：

```
src
├── Config.ts
├── ThemeProvider.tsx
├── api
├── assets
│   └── react.svg
├── component
│   ├── CopyText.tsx
│   └── RequiresHttps.tsx
├── i18n.ts
├── index.css
├── locales.json
├── main.tsx
├── view
│   ├── ErrorPage.tsx
│   └── Login.tsx
└── vite-env.d.ts
```

那么，我只要在`tsconfig.json`里的`compilerOptions`添加`"baseUrl": "./src"`，那么我在`main.tsx`里面可以以如下的形式引用：

```tsx
import ThemeProvider from "ThemeProvider";
// Also can be
import ThemeProvider from "./ThemeProvider";
```

但是，现在第一种方式用不了了，或许VSCode还能正常识别，但是用vite启动服务器的时候就会找不到包。

这个时候只要安装这个包到dev：`https://github.com/aleclarson/vite-tsconfig-paths`

随后把配置换成这个：

```ts
import { defineConfig } from 'vite'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  // 本来是：plugins: [react()],
  plugins: [tsconfigPaths()],
})
```

就可以自动的从`tsconfig.json`里面导入path，这样一来，就不用写[resolve.alias](https://vitejs.dev/config/shared-options.html#resolve-alias)了。

因为毕竟写alias，我看大多数的方案也是做成这样：

```ts
// vite.config.ts
{
  resolve: {
    alias: [
      { find: '@', replacement: path.resolve(__dirname, 'src') },
    ],
  },
  // ...
}
```

导入的时候就是：

```tsx
import ThemeProvider from "@/ThemeProvider";
```

我仍然不太喜欢，而且对于老项目，需要批量更改import着实是个负担。