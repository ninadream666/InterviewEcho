import json
import os

base_dir = os.path.join(os.path.dirname(__file__), '../knowledge-base/web-frontend/questions')
os.makedirs(base_dir, exist_ok=True)

technical = []

# --- HTML/CSS ---
html_css = [
    ("什么是HTML语义化？有哪些优点和常见标签？", "HTML语义化是根据内容的结构选择合适的标签（如header, nav, article）。优点：1. 代码可读性好；2. 机器友好，利于SEO；3. 无障碍访问。常见标签：header, main, footer, section, aside。", ["代码可读性", "SEO优化", "无障碍访问"], "HTML/CSS", "easy"),
    ("src与href的区别？", "href用于建立文档与资源的联系（如link引入CSS），是并行下载，不阻塞文档解析；src用于替换当前元素内容（如script、img），下载时会暂停文档主线程解析，直到加载和执行完毕。", ["href并行不阻塞", "src替换当前元素", "阻塞DOM解析"], "HTML/CSS", "easy"),
    ("script标签中 defer 和 async 的区别是什么？", "两者都用于异步加载脚本。区别：async下载完后立即执行，执行顺序不可控；defer在下载完后，会等待DOM解析完毕（DOMContentLoaded前）再按顺序执行。", ["异步机制", "执行时机", "顺序控制"], "HTML/CSS", "medium"),
    ("重排(Reflow)和重绘(Repaint)是什么？如何进行优化？", "重排指元素尺寸/位置变化导致重新计算布局；重绘指元素外观（颜色/背景）改变，不影响布局。重排必定引发重绘。优化：合并DOM修改，使用DocumentFragment，利用GPU加速（transform/opacity只会引发合成），脱离文档流。", ["重排布局", "重绘外观", "GPU硬件加速合成层"], "HTML/CSS", "medium"),
    ("谈谈BFC(块级格式化上下文)及触发条件", "BFC是一个独立的渲染区域。触发条件：根元素、float不为none、position为absolute/fixed、overflow不为visible、display为flex/inline-block等。用法：清除内部浮动避免塌陷、防止margin纵向重叠、实现自适应多栏布局。", ["独立渲染区", "触发条件", "解决塌陷/重叠"], "HTML/CSS", "hard"),
    ("CSS实现水平垂直居中常用方案有哪些？", "1. Flex：display:flex; justify-content:center; align-items:center; 2. 绝对定位+transform: translateY(-50%) translateX(-50%); 3. 绝对定位+margin:auto (需定宽高); 4. Grid: display:grid; place-items:center;", ["Flexbox", "Absolute+Transform", "Grid"], "HTML/CSS", "medium")
]

# --- JavaScript ---
javascript = [
    ("深入理解JS闭包(Closure)及其产生的问题？", "闭包指函数与其词法环境的引用捆绑在一起。允许内层函数访问外层函数作用域。用途：实现私有变量、柯里化、防抖节流。缺点：外部变量的引用被保留不会被垃圾回收，使用不当易造成内存泄漏，需手动置为null。", ["词法作用域", "数据私有化", "内存泄漏风险"], "JavaScript", "medium"),
    ("JS中this的指向规则及箭头函数的特点？", "this的指向由函数的运行时调用方式决定：1. 普通函数默认绑定全局（严格模式undefined）；2. 对象方法调用隐式绑定该对象；3. call/apply/bind显式绑定；4. new绑定实例。箭头函数没有自己的this，其this由外层词法作用域决定，不可被call/bind修改。", ["运行时动态绑定", "四大绑定规则", "箭头函数词法穿透"], "JavaScript", "medium"),
    ("简述原型(Prototype)与原型链(Prototype Chain)？", "每一个引用类型对象都有 `__proto__` 指向其构造函数的 `prototype` 对象。当访问属性时，如果对象自身没有，就会顺着 `__proto__` 向上层层找，最终到 `Object.prototype.__proto__`(null)为止，形成原型链。这是JS实现继承的基础。", ["__proto__与prototype", "向上委托查找变", "继承机制"], "JavaScript", "hard"),
    ("前端防抖（Debounce）和节流（Throttle）的区别？", "防抖：高频触发时，只在最后一次操作等待设定的时间后才执行（如搜索框实时联想，不断输入不发请求，停下才发）。节流：高频触发时，规定时间内只执行一次（如页面滚动监听，强制每秒最多触发一次）。两者都用于性能优化降低执行频率。", ["防抖看最后一次", "节流看时间间隔", "高频事件优化"], "JavaScript", "medium"),
    ("什么是JS的事件循环(Event Loop)机制？宏任务与微任务的区别？", "JS单线程通过事件循环处理异步。执行栈清空后，首先执行当前所有的微任务队列，再取出一个宏任务执行，完成后再次清空微任务队列。宏任务：setTimeout, setInterval, I/O；微任务：Promise.then/.catch代码块, MutationObserver, process.nextTick(优先级最高)。", ["单线程异步模型", "宏微任务划分", "微任务穿插时机"], "JavaScript", "hard"),
    ("深拷贝与浅拷贝的区别？如何手写实现一个深拷贝？", "浅拷贝只复制对象的第一层，嵌套的引用类型指向同一内存地址（如Object.assign）。深拷贝会递归复制所有层级，形成独立新对象。JSON.parse(JSON.stringify())是最简单深拷贝，但忽略函数和Symbol，且无法解决循环引用。手写需通过递归，并且用 WeakMap 记录已拷贝的节点解决循环引用。", ["引用地址差异", "JSON方法的缺陷", "递归与WeakMap防环"], "JavaScript", "hard"),
    ("JS垃圾回收机制(Garbage Collection)是怎样的？", "主要有两种策略。1. 引用计数（老旧）：通过追踪值被引用的次数，0次则回收，致命缺点是循环引用无法回收。2. 标记清除（现代主流）：从根对象(window)开始遍历，标记不可达的对象也就是垃圾进行回收。V8引擎进一步引入分代回收，新生代用Scavenge复制算法，老生代用标记清除和标记压缩。", ["引用计数的局限", "标记清除根查找", "V8分代式垃圾回收"], "JavaScript", "hard"),
    ("let、const 和 var 有什么区别？", "1. var有函数/全局作用域，let/const是块级作用域。2. var存在变量提升（初始化undefined），let/const存在暂时性死区（提升但不初始化，提前访问报错）。3. var允许重复声明，let/const不允许。4. const必须赋初始值且基本类型引用不可变，但若是对象可以修改其属性。", ["块级作用域", "暂时性死区(TDZ)", "可变性管控"], "JavaScript", "easy")
]

# --- ES6与异步编程 ---
es6 = [
    ("Promise有哪些常用方法？Promise.all和Promise.race的区别？", "实例方法用then/catch/finally。类方法：1. Promise.all()接收Promise数组，所有都成才走then返回数组，存在一个失败立马走catch；2. Promise.race()谁先出结果无论成功失败都返回谁；3. Promise.allSettled()等待所有都执行完，返回各自状态的数组，不短路。", ["all处理全部", "race短路竞争", "allSettled全覆盖"], "ES6与异步编程", "medium"),
    ("async/await 比 Promise 的链式调用好在哪里？", "async/await 是建立在 Promise 基础之上的语法糖，使异步代码写法更像同步代码，逻辑更直观，避免了 Promise 嵌套带来的冗长链式 `.then()`。通过 try/catch 可以直接同步捕获异步和同步的异常，而在多重依赖（比如异步D依赖异步C依赖异步B）时可读性呈现碾压级优势。", ["同步风格代码", "try/catch统一捕获", "无回调地狱"], "ES6与异步编程", "medium")
]

# --- Vue ---
vue = [
    ("简述Vue的双向数据绑定原理（Vue2与Vue3的区别）？", "Vue是数据劫持+发布订阅模式。Vue2使用 Object.defineProperty 劫持getter做依赖收集，setter做派发更新，缺点是无法监听到对象属性的新增/删除，以及通过索引改变数组（Vue2重写了内部7种数组方法作为Hack）。Vue3使用 ES6的 Proxy 直接代理整个对象，支持监听深层新增/删除和数组索引，并配合 Reflect 对对象进行操作，性能更优。", ["defineProperty与局限", "Proxy全代理", "依赖收集与派发更新"], "Vue/React核心", "hard"),
    ("Vue中组件通讯的方法有哪些？", "1. Props / $emit，最基础的父子通讯；2. provide / inject，用于祖先与子孙跨级通讯；3. Vuex / Pinia，全局状态管理器；4. EventBus (Vue2)，通过全局事件总线广播；5. ref 获取子组件实例直接调用方法；6. $attrs 与 $listeners 透传未声明的属性。", ["父子通讯", "跨级通讯", "系统级状态管理"], "Vue/React核心", "medium"),
    ("Vue的生命周期钩子有哪些？分别适合做什么？", "创建阶段：beforeCreate(无数据), created(有数据,常做初始请求)。挂载阶段：beforeMount, mounted(真实DOM挂载完成,适合DOM操作/实例化图表)。更新阶段：beforeUpdate, updated。销毁阶段：beforeDestroy(极其重要，用于解绑全局事件、清空定时器、销毁第三方实例), destroyed。Vue3改为 setup 及 onMounted/onUnmounted等。", ["挂载DOM操作(mounted)", "清理内存(beforeDestroy)", "生命周期流转"], "Vue/React核心", "medium"),
    ("为什么v-if和v-for不建议一起使用？", "Vue2中，v-for的优先级高于v-if，意味着哪怕v-if是false，每个循环的节点都会先被创建一遍然后销毁，极大浪费性能。Vue3中反转了优先级，v-if优先级高于v-for，但这会导致v-if中无法访问v-for里的变量引发报错。最优解：由于计算属性(computed)先过滤数组，再给v-for渲染。", ["优先级机制冲突", "性能消耗(Vue2)", "提倡使用Computed预处理"], "Vue/React核心", "medium")
]

# --- React ---
react = [
    ("React中虚拟DOM和Diff算法的原理是什么？", "虚拟DOM是用JS对象描述的真实DOM树，避免直接操作DOM带来高昂代价。React Diff采用同层比较：1. Tree Diff，两棵树同层比较，不同直接删掉重建；2. Component Diff，组件类型不同直接替换；3. Element Diff，利用唯一的 key 标识同层兄弟节点的位置移动而不是销毁重建，所以列表渲染中 key 至关重要。", ["JS对象抽象", "同层比较机制", "key复用原则"], "Vue/React核心", "hard"),
    ("React 16架构为什么要引入 Fiber？", "React 15的 Stack Reconciler 是递归同步更新DOM树，层级很深时会导致主线程被长时间占用，引发页面掉帧和输入卡顿。Fiber将其改为基于链表的渐进式渲染结构，把大任务碎片化（时间切片 Time Slicing）。Fiber机制具有挂起、恢复和优先级调度的能力，从而优先响应用户的交互等高优任务。", ["解决主线程阻塞", "Time Slicing时间碎片", "可中断与优先级调度"], "Vue/React核心", "hard"),
    ("React Hooks 中 useEffect 的依赖数组有哪些情况？", "1. 不传依赖：组件每次渲染(Render)都会执行。2. 传空数组 `[]`：相当于 `componentDidMount`，只在组件第一次渲染挂载时执行。3. 传参 `[a, b]`：只有当a或b发生变化时才会执行。此外如果在 effect 中返回了一个清理函数，则相当于 `componentWillUnmount`，在卸载前执行。", ["每次执行(无参)", "挂载阶段执行([])", "依赖监听及清理函数"], "Vue/React核心", "easy")
]

# --- 计算机网络 & 浏览器 ---
network = [
    ("从输入URL到页面渲染完成发生了什么？(非常高频)", "1. DNS解析，把URL转IP。2. 建立TCP三次握手连接。3. 客户端发送HTTP请求。4. 服务端处理并返回响应报文。5. 浏览器渲染：解析HTML生成DOM树，解析CSS生成CSSOM树，两者合并成渲染树(Render Tree)。6. 进行布局(Layout)，计算各节点位置/尺寸。7. 绘制(Paint)，绘制像素到屏幕。 8. 建立TCP四次挥手断开。", ["DNS与TCP过程", "渲染机制(DOM+CSSOM=RenderTree)", "Layout与Paint阶段"], "网络与浏览器", "hard"),
    ("TCP 的三次握手和四次挥手过程及意义？", "三次握手是为了确认双方的接收和发送能力正常，防止滞留的冗余连接发到服务端。过程：C发SYN -> S回SYN+ACK -> C发ACK。四次挥手为了全双工通道能安全关闭。过程：C发FIN -> S回ACK（半关闭，S可能还在发数据） -> S发FIN -> C回ACK。客户端还会等待2MSL防最后ACK丢包。", ["双向发送接收确认", "历史连接冗余防范", "全双工下的分别关闭"], "网络与浏览器", "hard"),
    ("前端跨域的原因及常见的解决方案有哪些？", "产生原因：浏览器的同源策略（协议、域名、端口必须完全一致）对XHR/Fetch及DOM的限制。解决方案：1. CORS (跨域资源共享)，最常用，后端设置Access-Control-Allow-Origin等响应头。2. JSONP，利用script标签无跨域限制，借此发送GET请求拿执行回调。3. Nginx反向代理或Node中间件代理（服务端之间通信无同源限制）。", ["同源策略", "CORS", "反向代理无限制"], "网络与浏览器", "medium"),
    ("浏览器缓存机制（强缓存与协商缓存）是怎样的？", "浏览器请求资源优先检视缓存。强缓存：未过期(Cache-Control里的max-age或Expires指定的时间)直接返回本地Status 200(from cache)，不发请求网络。协商缓存：如果强缓存失效，浏览器发送带有Etag/Last-Modified的请求给服务端。如果服务端判断资源未修改，则返回304 Not Modified，浏览器继续用旧缓存。如果修改了发200和新资源。", ["强缓存(Cache-Control)", "协商缓存(Etag/304)", "网络层降压策略"], "网络与浏览器", "medium")
]

# --- 前端工程化 ---
engineering = [
    ("Webpack中 Loader 和 Plugin 的区别是什么？", "Loader本质是转换器。Webpack默认只认识JS/JSON，Loader允许将其转化处理非JS模块（如 babel-loader 转ES6，css-loader处理样式）。Plugin本质是插件，利用Webpack提供的钩子(Hooks)在构建的各个生命周期注入逻辑扩展功能（如 HtmlWebpackPlugin生成模板，TerserPlugin压缩代码，SplitChunks分包等）。", ["Loader处理模块转换", "Plugin拦截生命周期", "各自典型应用库"], "前端工程化", "medium"),
    ("什么是 Tree Shaking？它的原理是什么？", "Tree Shaking翻译为摇树，是用来在打包阶段移除JavaScript中未被引用的死代码消除(Dead Code Elimination)。原理：依赖于 ES6 Module (import/export) 的静态结构特性。因为ESM是在编译时确定模块依赖，而不像CommonJS在运行时确定。Webpack分析代码流向，找出没被使用的模块并在Terser压缩期间删掉它们。", ["消除死代码(Dead Code)", "基于ESM静态分析", "构建体积压缩"], "前端工程化", "hard"),
    ("Vite 为什么比 Webpack 开发环境快那么多？", "Webpack在启动时需要先从入口出发分析所有依赖、通过Loader转译打包成Bundle再交由服务器，项目变大速度指数变慢。Vite 利用了现代浏览器原生支持 ESM ( `<script type=\"module\">` )的特性，不对代码预打包，直接启动服务器。当浏览器请求特定模块时，Vite在服务端再进行按需编译（用到谁转谁），极大地提升了冷启动与热更新速度。", ["原生ESM无打包启动", "按需按量编译响应", "打包思路的时间复杂度降维"], "前端工程化", "hard")
]

for arr in [html_css, javascript, es6, vue, react, network, engineering]:
    for q, a, p, sec, diff in arr:
        technical.append({"id": f"tech_{str(len(technical))}", "job_type": "web-frontend", "category": "technical", "question": q, "reference_answer": a, "key_points": p, "difficulty": diff, "section": sec})

scenarios = [
    {
        "id": "scn_101",
        "job_type": "web-frontend",
        "category": "scenario",
        "question": "（经典场景）如果后端一次性返回10万条或巨量列表数据，前端如何做到渲染不卡顿？",
        "reference_answer": "硬渲染会导致浏览器主线程死锁。1.【虚拟列表】核心方案：不管数据多大，只渲染可视区域内计算出能显示的几十个DOM节点和上下少量缓冲区，当滚动时动态替换数据。2.【时间切片】：基于 requestAnimationFrame，配合 DocumentFragment 分批次每次向页面插入几百条，防止掉帧卡死。3.【业务层面推翻】与后端协商，改为真正的滚动分页 / 下拉加载。",
        "key_points": ["虚拟列表(Virtual List)", "时间切片分批插入", "推翻协商分页"],
        "difficulty": "hard",
        "section": "海量数据渲染"
    },
    {
        "id": "scn_102",
        "job_type": "web-frontend",
        "category": "scenario",
        "question": "首屏加载白屏时间过长，作为前端工程师，你会如何排查并制定优化方案？",
        "reference_answer": "1.【分析阶段】：利用 Chrome Network 分析瀑布流，或 Lighthouse 跑分确定瓶颈是加载（网络包太大）还是解析执行阻塞（主线程爆表）。2.【体积优化】：前端路由采用懒加载分割(Bundle 分片)；开启 Gzip/Brotli，图片用 WEBP/雪碧图，抽离体积庞大的第三方库走CDN。3.【渲染优化】：加入骨架屏改善体验感知。4.【网络链路】：HTTP/2 多路复用。5. 对外 C 端项目直接重构接入 SSR / SSG 预渲染 HTML 降低 FCP。",
        "key_points": ["利用工具定量分析瓶颈", "路由异步拆包切割", "SSR服务端渲染解决FCP", "开启Gzip/CDN加速"],
        "difficulty": "hard",
        "section": "性能排查与优化"
    },
    {
        "id": "scn_103",
        "job_type": "web-frontend",
        "category": "scenario",
        "question": "监控经常报警说某个SPA页面出现内存泄漏甚至应用崩溃崩溃（OOM）。你该如何定位和修复？",
        "reference_answer": "使用 Chrome DevTools 的 Memory 面板，录制一段时间前后的堆快照（Heap Snapshot），或者使用 Allocation Timeline 观察内存一直走高的阶梯波。通常漏水点排查：1. 被遗忘的 setInterval/setTimeout 没有被 clearInterval。2. 在 Vue/React 组件挂载时给 `window` 绑定的 scroll/resize 全局事件，在组件销毁时没有解绑。3. Echarts 图表实例等复杂第三方库没有调用其 dispose 销毁。修复只要在 unmounted/beforeDestroyed 或者 useEffect 的 return 清理函数中处理掉悬空引用即可。",
        "key_points": ["Memory堆快照对比寻找游离DOM", "组件卸载未抛弃定时器", "第三方库及全局事件未解绑清理"],
        "difficulty": "hard",
        "section": "线上故障排查"
    },
    {
        "id": "scn_104",
        "job_type": "web-frontend",
        "category": "scenario",
        "question": "如何使用JS手写实现带最大发请求条数限制的异步并发控制？（例如下载批量大文件但最多1次发3个）",
        "reference_answer": "考点是手写调度器机制避免峰值导致浏览器崩或防 CC 封禁。实现维护两个变量：正在运行任务数量的计数器(正在跑的数量 `activeCount`)，以及待执行的任务队列 `queue`。在触发时启动至多上限（如3个）个任务，当其中任何一个请求对应的 Promise 通过 .finally() 落敲时，`activeCount` 减一，并立刻从 `queue.shift()` 中取出下一个任务通过递归压入执行，从而保证跑满最大限制持续输出。",
        "key_points": ["Promise状态拦截", "并发队列池动态吐出", "解决网络拥塞导致被拦截"],
        "difficulty": "hard",
        "section": "网络并发调度"
    },
    {
        "id": "scn_105",
        "job_type": "web-frontend",
        "category": "scenario",
        "question": "业务要求用户在浏览商品巨长列表滑到 30 页以后去别的页面，返回需维持原来滚动高度和原数据，怎么实现前端状态缓存？",
        "reference_answer": "1. 框架级方案：利用 Vue 中的 `<keep-alive>` 加上 include 动态控制，让商品列表组件只挂起不销毁，重回页面直接切出该 DOM（React 可以使用 react-activation 插件或在顶层用 css的 display:none控制不卸载）。2. 状态存储方案：跳转详情页前，将当前已加载的数据、页码及滚动条高度 `scrollTop` 写入 Redux/Vuex 或 sessionStorage，用户返回时重新派发数据流并在 DOM 渲染 `nextTick` 中调用 `window.scrollTo` 滚动到原位。",
        "key_points": ["keep-alive 不卸载直达", "Vuex/Redux 状态长存", "scrollTop 记录与还原"],
        "difficulty": "medium",
        "section": "前端状态保持"
    },
    {
        "id": "scn_106",
        "job_type": "web-frontend",
        "category": "scenario",
        "question": "大文件上传（例如500MB到数GB的视频文件）应该怎么设计？如果中断了该如何做到断点续传？",
        "reference_answer": "【分片上传】：通过文件的 File 或 Blob 对象的 `.slice()` 方法，设置恒定块大小（例如2MB）切成多个小片段。把分片按照顺数索引使用多个 Ajax 并发派发到服务器，发完再发一个“合并指令”，服务端把收到的文件流拼回主文件。 【断点续传与秒传】：上传前根据文件的内容计算生成 Hash(MD5)作为标识去向服务端询问，如果已全存在则直接显示“秒传”成功；如果传了一半异常断开，服务端会告知目前收到了哪些索引分片，前端只过滤出剩下的再传即可。",
        "key_points": ["Blob.slice对象分片切片", "Spark-md5内容摘要获取文件指纹", "索引计算补传以防网络断线"],
        "difficulty": "hard",
        "section": "工程架构场景"
    },
    {
        "id": "scn_107",
        "job_type": "web-frontend",
        "category": "scenario",
        "question": "如何防止前端受到 XSS 攻击与 CSRF 攻击？",
        "reference_answer": "【XSS跨站脚本攻击】：防注入恶意脚本。解决：绝不能信任用户的输入，对输入进行转义/HTML Entities净化，避免滥用 `v-html` 或 `dangerouslySetInnerHTML`。配置 CSP 头部。由后端配合做强转义。【CSRF跨站请求伪造】：利用用户已登录留存的Cookie伪造请求。解决：把接口防线转到Cookie之外。如 校验 Referer 同源头信息、要求携带随页面生成的复杂Token(放到Authorization请求头而不仅是Cookie)。如果用Cookie，强行加上 `SameSite=Strict` 属性禁止第三方跨域携带。",
        "key_points": ["XSS应对HTML转义和CSP", "CSRF核心在于Cookie被默认借用", "Token头校验和SameSite防止CSRF"],
        "difficulty": "medium",
        "section": "前端安全防护"
    }
]

projects = [
    {
        "id": "prj_201",
        "job_type": "web-frontend",
        "category": "project",
        "question": "请讲一个让你最自豪的/技术挑战最大的项目，你扮演了什么角色取得了什么结果？",
        "reference_answer": "【遵循 STAR 原则(情境、任务、行动、结果)】。不要只答业务增删改查。\n参考：【情境】项目是一个存在大量图表展示和复杂表单重构配置的业务系统，原有架构老旧（或者遇到严重卡顿）。【任务】作为前端核心/负责人主导了系统的基建和重构改造。【行动】从框架层面挑选Vue3+Pinia/React+Zustand重架构，抽离15+公用基础业务组件推送到内部镜像。采用懒加载和重写渲染逻辑(或者canvas画布改写)破除老系统的卡顿。【结果】提高了团队协同效率百分之30%，Lighthouse跑分LCP缩短1秒以上。",
        "key_points": ["STAR原则讲述全局闭环", "跳脱CRUD，体现架构思考", "使用数据支撑业务收益"],
        "difficulty": "medium",
        "section": "项目架构与复盘"
    },
    {
        "id": "prj_202",
        "job_type": "web-frontend",
        "category": "project",
        "question": "在项目中碰到过特别难调优的性能问题吗？可以详细说说整个链路吗？",
        "reference_answer": "例如：接手时由于一个超大树形控件渲染卡废了应用。排查发现每点击一个节点就会引发顶级组件无脑下发导致全页面的 React/Vue Diff重排（深拷贝过度引发性能骤降）。我的干预优化是：1. 针对渲染机制使用 `React.memo` 或者 `SFC` 加依赖约束缓存避免无效重绘。2. 把树结构拍平为一维数组结合虚拟列表优化，DOM从几万个锐减到100个以内。最终 FPS 从30掉帧回稳到达 60，页面丝滑。",
        "key_points": ["利用性能监控分析瓶颈(Performance面板)", "阻截无关的脏重绘", "算法级降维改变渲染策略"],
        "difficulty": "hard",
        "section": "性能调优实战"
    },
    {
        "id": "prj_203",
        "job_type": "web-frontend",
        "category": "project",
        "question": "在前端团队内或者项目迭代中，你做过哪些工程化/基准建设的工作？",
        "reference_answer": "针对团队新人多、代码规范混乱的问题，我主导了【研发流水线增强】。1. 统一接入 ESlint、Prettier 以及 Git Husky 做提交卡点拦截(Lint-staged)，将规范固化。2. 编写了 CLI 提效工具及通用的脚手架模板，将新项目的开箱成本缩减到了2分钟。 3. 在构建层面排查了 Webpack 的冗余 Loader，引入 Vite 的 ES-build 转译把开发环境 HMR 热更新从数十秒提高到了毫秒级。",
        "key_points": ["Lint/Husky流水卡点机制规范化", "构建工具调参", "内部研发效能提效"],
        "difficulty": "hard",
        "section": "前端工程化落地"
    }
]

behavioral = [
    {
        "id": "bhv_301",
        "job_type": "web-frontend",
        "category": "behavioral",
        "question": "经常有紧急任务突然插队，并且产品给的时间非常紧，你甚至觉得做不完，这时候怎么应对排期？",
        "reference_answer": "绝对不一口回绝也不能硬接下来导致系统延期爆雷。步骤：1. 【划分优先级】运用重要/紧急四象限拆解，向提需人确认这个需的核心痛点。2. 【讨价还价减减法】进行需求妥协，商议出第一阶段上线的 MVP(最小可用产品版)先行。将高风险长链条的附属功能推入二期迭代。 3. 【向上管理寻求资源】将工时红线摆上台面请求主管帮助协调人力分摊开发，同时防备项目交付粗糙必须在项目复盘会议中提出建立更合理的发版流程规范。",
        "key_points": ["应用 MVP 思想砍需求减配", "优先级四象限管理", "向上管理和暴露风险寻找支援"],
        "difficulty": "medium",
        "section": "项目管理与排期"
    },
    {
        "id": "bhv_302",
        "job_type": "web-frontend",
        "category": "behavioral",
        "question": "遇到前后端对接时，发现后端开出的接口结构反人类、嵌套极深且响应很慢，还强行丢给前端处理，你会怎么办？",
        "reference_answer": "以“为了优化最终用户体验”为大前提（而不是推诿抱怨）。1. 客观摆出数据：用 Postman 等工具给出当前接口速度会导致白屏的数据报告，阐述在前端用JS强行清洗这类畸形结构造成维护成本陡增并容易引发异常崩溃。2. 给出替代方案草案：给出我心里理想的聚合 JSON 格式，看看是否可以协调中间加一层聚合。3. 【底线妥协】：如果在强时间压力下后端确实无法重构，我们可以写一层专门的适配层（Adapter）防腐或者在BFF (Node层)中专门转接过渡，但必须拉群报备PM及TL作为技术债录入文档。",
        "key_points": ["拿数据论证不合理性", "为用户体验(延时)担责作为压标利器", "提出解决方案及设计BFF防腐手段代替纯抱怨"],
        "difficulty": "medium",
        "section": "沟通协作"
    },
    {
        "id": "bhv_303",
        "job_type": "web-frontend",
        "category": "behavioral",
        "question": "如果工作中你和研发组长/TL在技术选型上产生了严重分歧（你的技术更潮他更保守），你一般怎么处理？",
        "reference_answer": "首先明确 TL 的考量更多在业务稳定性与学习成本上，这属于正常现象。我会采用【灰度验证兼论述】的做法。写一个小型 Demo 展示我推崇的新技术(比如从 Webpack 升到 Vite)能够确凿带来几十秒甚至量级上的冷启动时间减少的直接证据，并且列出该新旧技术的维护成本平滑迁移表和坑点。如果论证详尽后TL依然认为保守为上，我会执行最终决策。团队统一性大于个人主观偏好。",
        "key_points": ["尊重业务求稳", "数据和 Demo Proof 证明收益化解担忧", "大局为重服从统一性"],
        "difficulty": "medium",
        "section": "技术路线冲突解决"
    },
    {
        "id": "bhv_304",
        "job_type": "web-frontend",
        "category": "behavioral",
        "question": "线上系统突然出现P0级别故障，白屏了，作为接触对应模块的前端，你会怎么做？",
        "reference_answer": "1. 【首要止血规避影响】：必须先第一时间降级或切分支（通知运维回滚到最近稳定的版本上线），必须先让系统可用。 2. 【搜集定位】：止血后利用埋点系统（如 Sentry 等）、抓取用户操作日志以及排查最近的发版记录，拉出出问题的 SourceMap 层去精确寻找代码块。 3. 【复现排错】：本地复现边界条件，修复补丁。 4. 【事故复盘】：修复后必须撰写复盘文档反思为何这类问题突破了测试漏眼，制定相应的卡点手段（添加流水线单元测试/重绘测试校验）。",
        "key_points": ["第一要务回滚止血降低资损", "利用错误收集与监控捕获源头", "事故沉淀及研发防腐纠正"],
        "difficulty": "medium",
        "section": "应急处理能力"
    }
]

with open(os.path.join(base_dir, 'frontend_technical.json'), 'w', encoding='utf-8') as f:
    json.dump(technical, f, ensure_ascii=False, indent=4)

with open(os.path.join(base_dir, 'scenarios.json'), 'w', encoding='utf-8') as f:
    json.dump(scenarios, f, ensure_ascii=False, indent=4)

with open(os.path.join(base_dir, 'projects.json'), 'w', encoding='utf-8') as f:
    json.dump(projects, f, ensure_ascii=False, indent=4)

with open(os.path.join(base_dir, 'behavioral.json'), 'w', encoding='utf-8') as f:
    json.dump(behavioral, f, ensure_ascii=False, indent=4)
