import json
import os

base_dir = os.path.join(os.path.dirname(__file__), '../knowledge-base/web-frontend/questions')
os.makedirs(base_dir, exist_ok=True)

technical = [
    {
        "job_type": "web-frontend",
        "category": "technical",
        "question": "什么是HTML语义化？有哪些优点和常见标签？",
        "reference_answer": "HTML语义化是根据内容的结构选择合适的标签（如header, nav, article, section, footer等）。优点：1. 增加代码可读性，结构清晰，便于开发维护；2. 对机器友好，有利于SEO；3. 方便特殊设备（如屏幕阅读器）解析；4. 在没有CSS样式下也能呈现良好的结构。",
        "key_points": ["代码可读性", "SEO优化", "无障碍访问", "常见标签(header, section, main, article等)"],
        "difficulty": "easy",
        "section": "HTML基础"
    },
    {
        "job_type": "web-frontend",
        "category": "technical",
        "question": "script标签中 defer 和 async 的区别是什么？",
        "reference_answer": "两者都用于异步加载脚本以避免阻塞DOM解析。区别在于：async异步加载完成后立即执行，多个async脚本执行顺序不可控；defer异步加载完成后，会等待文档所有元素解析完成（DOMContentLoaded事件触发前）再执行，且能保证多个defer脚本按顺序执行。",
        "key_points": ["避免阻塞DOM解析", "执行时机(立即执行 vs DOM解析后执行)", "执行顺序保证"],
        "difficulty": "medium",
        "section": "HTML基础"
    },
    {
        "job_type": "web-frontend",
        "category": "technical",
        "question": "简述什么是重排(Reflow)和重绘(Repaint)？如何进行优化？",
        "reference_answer": "重排是当元素的尺寸、结构或属性变化引起浏览器重新渲染局部或全部文档。重绘是元素外观（如颜色、背景）改变但不影响布局时的重新绘制。重排必触发重绘。优化：1. 合并样式修改，使用class；2. 避免频繁读取引起重排的属性（如offsetHeight）；3. 离线DOM操作（DocumentFragment）；4. 利用GPU加速（transform, opacity）；5. 使用absolute脱离文档流。",
        "key_points": ["重排定义与触发条件", "重绘定义", "优化策略(GPU加速, 避免频繁读取等)"],
        "difficulty": "medium",
        "section": "CSS基础与性能"
    },
    {
        "job_type": "web-frontend",
        "category": "technical",
        "question": "谈谈你对BFC(块级格式化上下文)的理解？",
        "reference_answer": "BFC是一个独立的渲染区域，隔离了内部和外部的元素，内部元素的渲染不会影响外部。触发条件包括：处于根元素、float不为none、position为absolute或fixed、display为flex/inline-block等、overflow不为visible。应用场景：消除margin纵向重叠、清除内部浮动（防止父级高度塌陷）、实现自适应两栏布局。",
        "key_points": ["独立渲染区域", "触发条件(float, absolute, flex, overflow等)", "应用场景(margin重叠, 清除浮动)"],
        "difficulty": "medium",
        "section": "CSS基础与性能"
    },
    {
        "job_type": "web-frontend",
        "category": "technical",
        "question": "前端经典布局：圣杯布局与双飞翼布局的实现原理及区别？",
        "reference_answer": "两者的目的都是实现三栏布局（左右定宽，中间自适应）且中间优先渲染。圣杯布局通过在父容器上设置padding留出左右空间，利用float、负margin和相对定位(relative)将左右拉到正确位置；双飞翼布局则在中间区块内部嵌套子div设置margin留出空间，只利用float和负margin进行左右元素定位，不需要相对定位。",
        "key_points": ["三栏布局与优先渲染", "利用float和负margin", "预留空间的差异(父级padding vs 内层margin)"],
        "difficulty": "hard",
        "section": "CSS高级布局"
    },
    {
        "job_type": "web-frontend",
        "category": "technical",
        "question": "防抖（Debounce）和节流（Throttle）的区别及应用场景？",
        "reference_answer": "防抖是指在规定时间内多次触发只执行最后一次，适用于搜索框输入、窗口resize等操作；节流是指在规定时间内只执行一次，哪怕触发多次，适用于滚动条监听、频繁点击按钮、鼠标移动触发等高频操作。它们都能有效减少DOM操作和网络请求，提升性能。",
        "key_points": ["执行时机差别(最后一次 vs 规定频率)", "应用场景", "性能优化降低高频触发"],
        "difficulty": "medium",
        "section": "JavaScript基础"
    },
    {
        "job_type": "web-frontend",
        "category": "technical",
        "question": "什么是闭包(Closure)？它有哪些优缺点？",
        "reference_answer": "闭包是指函数可以记住并访问其词法作用域中的变量，即使该函数在其词法作用域之外执行。它本质上是函数和其周围状态组合的实体。优点是可以创建私有变量，避免全局污染，用于高阶函数或柯里化；缺点是闭包中引用的变量常驻内存，容易导致内存泄漏（需手动将变量置为null）。",
        "key_points": ["词法作用域", "私有变量/避免全局污染", "常驻内存与内存泄漏"],
        "difficulty": "medium",
        "section": "JavaScript基础"
    },
    {
        "job_type": "web-frontend",
        "category": "technical",
        "question": "简述JS的事件循环(Event Loop)机制以及宏任务、微任务的区别？",
        "reference_answer": "JS是单线程的，通过事件循环实现异步。执行过程：执栈空后，先检查微任务队列，清空微任务队列后再取出一个宏任务执行，完成后又去清空微任务队列。宏任务包括：setTimeout, setInterval, I/O, UI rendering等。微任务包括：Promise.then/catch/finally, MutationObserver, process.nextTick(Node)。",
        "key_points": ["单线程与异步机制", "宏任务分类", "微任务分类", "一次事件循环的执行顺序"],
        "difficulty": "hard",
        "section": "JavaScript基础"
    },
    {
        "job_type": "web-frontend",
        "category": "technical",
        "question": "前端跨域的解决方案有哪些？常用哪几种？",
        "reference_answer": "由于浏览器的同源策略（协议、域名、端口一致），会导致跨域。常见解决方案：1. CORS（主流）：后端配置Access-Control-Allow-Origin头；2. JSONP：利用script标签无跨域限制，只支持GET请求；3. Nginx反向代理或Node中间件代理（常见于开发环境webpack dev-server配置反向代理）；4. postMessage处理iframe通信；5. WebSocket协议。",
        "key_points": ["同源策略限制", "CORS", "Nginx反向代理", "JSONP及局限性"],
        "difficulty": "medium",
        "section": "网络与浏览器"
    },
    {
        "job_type": "web-frontend",
        "category": "technical",
        "question": "从输入URL到页面渲染完成发生了什么？(越详细越好)",
        "reference_answer": "1. DNS解析把URL解析为IP；2. 建立TCP三次握手连接；3. 客户端发送HTTP请求；4. 服务器响应并返回HTML；5. 浏览器解析页面：解析HTML构建DOM树，解析CSS构建CSSOM树，将两者合并生成渲染树（Render Tree）；6. 布局（Layout/Reflow），计算各元素位置和大；7. 绘制（Paint），根据计算将元素绘制到屏幕上；8. 四次挥手断开结束连接。",
        "key_points": ["DNS解析", "TCP三次握手", "DOM与CSSOM解析生成渲染树", "Layout与Paint的过程"],
        "difficulty": "hard",
        "section": "网络与浏览器"
    },
    {
        "job_type": "web-frontend",
        "category": "technical",
        "question": "Promise有哪些常见的方法？Promise.all和Promise.race的区别？",
        "reference_answer": "常见方法包含：then, catch, finally, resolve, reject。Promise.all()接收一个Promise数组，所有都成功才走then(返回结果数组)，只要有一个失败就走catch；Promise.race()也是接收数组，哪个Promise状态最先改变(无论成功失败)，就直接返回它的结果。Promise.allSettled()等待所有完成无论成功还是失败。",
        "key_points": ["then, catch, finally", "all: 具备短路特性失败", "race: 最快返回结果", "allSettled"],
        "difficulty": "medium",
        "section": "ES6高级编程"
    },
    {
        "job_type": "web-frontend",
        "category": "technical",
        "question": "简述Vue的双向数据绑定原理（Vue2与Vue3的差异）？",
        "reference_answer": "Vue2基于 Object.defineProperty 进行数据劫持，结合发布订阅模式（Dep/Watcher）实现，无法监听对象属性的添加/删除以及数组索引直接修改。Vue3使用 ES6的 Proxy 进行代理，可以直接监听对象和数组的变化，并配合 Reflect 操作对象，支持深层代理（按需懒代理），性能和扩展性大幅提升。",
        "key_points": ["Vue2: Object.defineProperty", "数据劫持结合发布订阅", "Vue3: Proxy与Reflect", "代理数组与深层响应优化"],
        "difficulty": "hard",
        "section": "Vue框架"
    },
    {
        "job_type": "web-frontend",
        "category": "technical",
        "question": "什么是虚拟DOM(Virtual DOM)？为什么需要虚拟DOM？",
        "reference_answer": "虚拟DOM是用JS对象模拟真实的DOM树结构和属性。每次状态更新时，框架会生成新的虚拟DOM，与旧的虚拟DOM进行Diff算法对比，将所有的差异收集起来再批量更新到真实DOM上。需要它的原因：1. 提升性能（减少直接且频繁的DOM重排重绘）；2. 提供跨平台的可能（如Weex、React Native），使得底端渲染不仅仅局限于浏览器。",
        "key_points": ["JS对象模拟DOM结构", "Diff算法比较差异批量更新", "跨平台能力与框架底座"],
        "difficulty": "medium",
        "section": "Vue/React核心原理"
    },
    {
        "job_type": "web-frontend",
        "category": "technical",
        "question": "在React中，useEffect的依赖数组有几种情况？",
        "reference_answer": "1. 依赖数组不传：每次组件重新渲染都会执行，并可能导致死循环；2. 依赖数组为空[]：仅在组件首次挂载（DidMount）和卸载时执行清理函数（WillUnmount）；3. 依赖数组有值[a, b]：只有当数组内的依赖项在重渲染期间发生变化时，才会执行effect。",
        "key_points": ["不传引发频繁执行", "空数组模拟初始化与卸载", "包含依赖项时的更新时机"],
        "difficulty": "easy",
        "section": "React框架"
    },
    {
        "job_type": "web-frontend",
        "category": "technical",
        "question": "Webpack中loader和plugin的区别是什么？",
        "reference_answer": "Loader本质上是转换器，由于Webpack只认识JS和JSON，Loader将非JS文件（如CSS、图片、TS等）转化为Webpack能识别的模块，如babel-loader, css-loader；Plugin是插件，扩展Webpack功能，在Webpack构建周期的各个生命周期节点广播事件，执行特定任务，如压缩代码（TerserPlugin）、打包分离、注入环境变量等。",
        "key_points": ["Loader是文件转换器/处理机制", "Plugin是扩展插槽/影响构建周期", "常用loader与plugin举例"],
        "difficulty": "medium",
        "section": "前端工程化"
    }
]

scenarios = [
    {
        "job_type": "web-frontend",
        "category": "scenario",
        "question": "如果后端一次性返回10万条数据，前端如何不卡顿地渲染？",
        "reference_answer": "由于直接生成10万个DOM节点会造成浏览器渲染卡死引发重排阻塞，有三种方案：1. 虚拟列表（Virtual List），计算可视区域内可渲染的元素数量，结合滚动条事件只渲染视口内与缓冲区的DOM节点，这属于最优解；2. 结合requestAnimationFrame并用DocumentFragment分批次插入DOM（如每次切割插入100条）；3. 与后端协商推翻该方案，强制分页或下拉加载（最推荐）。",
        "key_points": ["限制DOM渲染开销", "实现虚拟列表思想", "时间切片与requestAnimationFrame", "倒逼重构分页方案"],
        "difficulty": "hard",
        "section": "大厂场景题"
    },
    {
        "job_type": "web-frontend",
        "category": "scenario",
        "question": "在单页面应用(SPA)中，如果发现首屏加载极慢白屏严重，你是如何分析和优化的？",
        "reference_answer": "1. 发现问题：通过Chrome Network/Performance或是Lighthouse查看首屏指标(FCP/LCP)。2. 原因多为打包体积过大、缺乏缓存、接口请求慢等。3. 代码层面：路由懒加载(异步组件)，第三方库按需引入。4. 工程化层面：Gzip/Brotli压缩、分离公共依赖(SplitChunks)、提取CSS，开启Tree Shaking。5. 网络层面：静态资源上CDN，使用HTTP/2；如必要直接做骨架屏或考虑服务端渲染(SSR/SSG)。",
        "key_points": ["打包体积优化分析", "路由按需加载与切割", "静态资源CDN与Gzip", "骨架屏或服务端渲染(SSR)"],
        "difficulty": "hard",
        "section": "性能优化排查"
    },
    {
        "job_type": "web-frontend",
        "category": "scenario",
        "question": "多个请求并发获取数据，如何实现请求的“并发控制”（例如最多同时发送3个请求）？",
        "reference_answer": "这通常用手写一个并发控制器实现。内部维护一个正在执行的任务数量的计数器(count或者池子)和一个等待执行队列。通过循环将任务推进执行队列直到上限3次。每当一个Promise敲定（使用.then和.catch），就把自己移出执行池并降低count，然后再从等待队列里出队下一个并触发。可作为Promise的经典面试手写题考察。",
        "key_points": ["维护并发队列与当前执行状态", "Promise处理与递归拿取任务", "控制发送上限防服务器压力"],
        "difficulty": "hard",
        "section": "网络与异步并发"
    },
    {
        "job_type": "web-frontend",
        "category": "scenario",
        "question": "用户在长列表页面滚动到了第30页点击进入详情，返回时怎么保留滚动位置与列表数据？",
        "reference_answer": "Vue中可利用 `<keep-alive>` 结合 router-meta 中的字段（并设置 `scrollTop` 保存在 vuex 或路由参数），实现组件的不卸载；React 可以采用三方库 `react-activation` 类似的功能，或将列表数据缓存在 Redux/Context 并在重挂载时以 `window.scrollTo` 恢复位置。对于极其复杂的电商业务甚至可以通过前端把分页接口存储于 sessionStorage 手动复原。",
        "key_points": ["keep-alive状态缓存机制", "滚动条高度的记录与恢复", "状态管理库数据的持久化"],
        "difficulty": "medium",
        "section": "前端状态保持"
    },
    {
        "job_type": "web-frontend",
        "category": "scenario",
        "question": "线上监控突然告警：某个页面出现大量内存泄漏。作为前端你如何定位和处理？",
        "reference_answer": "1. 复现现象：使用Chrome DevTools的Memory面板，录制堆快照（Heap Snapshot）或分配时间线，对比操作前后的内存增量。2. 排查漏点：通常发生在未被清理的定时器/延时器、未注销的全局事件解绑、闭包引用了巨大对象、以及Vue/React中组件销毁但引用的某些第三方库（如Echarts图表）实例未dispose等情况。3. 编写复现场景，修复并在`beforeDestroy` / `useEffect return`中清理内存。",
        "key_points": ["内存泄漏排查工具Memory", "常见DOM脱离与悬空引用", "闭包与定时器的未清理", "组件生命周期的妥善利用"],
        "difficulty": "hard",
        "section": "线上排查"
    }
]

projects = [
    {
        "job_type": "web-frontend",
        "category": "project",
        "question": "你在XX项目中担任了什么角色？该项目的整体前端架构是怎样的？",
        "reference_answer": "【考察要点：能否脱离CRUD，宏观认识系统】采用STAR法则回答：1. Situation（背景）：项目目标是什么、业务痛点是什么。2. Task：我在其中扮演核心研发角色，主导了从0到1或者是重构的落地。3. Action：从技术栈选型（Vue3+Vite+Pinia/Taro）、模块拆分、微前端基座搭建、公用组件库沉淀及监控日志上报做了架构设计。4. Result：最终有效支持前端几百个页面的运转，缩短了新人接手成本。",
        "key_points": ["STAR法则叙述", "技术选型的合理性与沉淀", "架构维度的思考深度"],
        "difficulty": "medium",
        "section": "项目架构"
    },
    {
        "job_type": "web-frontend",
        "category": "project",
        "question": "在你的项目中遇到的技术挑战/难点（最自豪的功能）是什么？怎么解决的？",
        "reference_answer": "本题无固定答案，主要看深度。常见高分回答范例：1. 性能类：业务存在超大量数据或复杂动画，通过Time Slicing/Web Worker/canvas离屏渲染破除了主线程阻塞，最终帧率提升了50%。2. 基建类：团队早期缺乏开发规范，业务代码与组件冗余，自己主导抽离封装并搭建私有npm，推行eslint流水线卡点，使得团队人效提升并减少了X%线上bug。强调：必须有对比数据和方法论。",
        "key_points": ["提炼遇到的难题核心", "技术与方案对比的深入度", "使用客观数据呈现成果"],
        "difficulty": "hard",
        "section": "技术深度与攻坚"
    },
    {
        "job_type": "web-frontend",
        "category": "project",
        "question": "关于你在简历中提到的性能优化，说一下具体落地的细节和收益？",
        "reference_answer": "【考察优化不是简单背八股】我主要分为两部分做：1. 打包优化方向：通过体积分析工具发现某些强绑定的包过大，于是将其重构为按需引用、或提取为CDN公用，利用Gzip+缓存；2. 运行时方向：项目中某些复杂组件造成严重交互卡顿，我利用了React.memo / useMemo或者Vue中的函数式代码重构及避免不必要渲染重绘。通过前后Lighthouse跑分，LCP下降到1.2s。",
        "key_points": ["监控链路发现问题", "具体代码操作", "优化带来的实际业务价值(数据化)"],
        "difficulty": "hard",
        "section": "项目优化实践"
    }
]

behavioral = [
    {
        "job_type": "web-frontend",
        "category": "behavioral",
        "question": "遇到前后端对接时，发现后端的接口设计严重不合理（如层级太深又很慢），你会如何沟通？",
        "reference_answer": "1. 保持客观：不会单纯抱怨，而是把响应慢会导致前端白屏体验下降的风险摆出来，或者层级太深导致的适配额外逻辑成本。 2. 提供论证：利用Postman或接口录制展示目前的耗时，并提出自己认为优化的JSON结构（比如要求拉平冗余字段、聚合某些小接口）。3. 协商平衡：如果是多方依赖不好动，则提供折中方案如加BFF中间层Node聚合、或增加字段标记，必要情况下拉上技术Leader决策以保障项目质量。",
        "key_points": ["以用户体验/系统风险为出发点", "带着替代方案沟通", "不带情绪和边界意识解决问题"],
        "difficulty": "medium",
        "section": "跨部门协作"
    },
    {
        "job_type": "web-frontend",
        "category": "behavioral",
        "question": "如果同时有多个任务紧急插队，且时间给的很短，你会如何排期和处理？",
        "reference_answer": "首先绝不能直接全部接下或全部拒绝。1. 梳理优先级资源池：按照（重要且紧急、重要不紧急、紧急不重要）等四象限分类；2. 与产品沟通降低预期或者探讨MVP（最小可行性产品）阶段性上线方案；3. 同步风险：立即反馈给上级或PM目前的排期容量，抛出现有资源上限；4. 如果确实要做，寻求团队成员资源协助分配，并总结项目后需要避免规划不合理的复盘。",
        "key_points": ["优先级管理与四象限", "利用MVP思想拆解上线", "向上管理暴露风险寻找资源"],
        "difficulty": "medium",
        "section": "项目管理"
    },
    {
        "job_type": "web-frontend",
        "category": "behavioral",
        "question": "你在团队中扮演什么角色？你是如何带新人或者把知识沉淀的？",
        "reference_answer": "主要想考察领导力与知识传承。回答思路：在日常代码中会主动承担复杂核心模块并在PR (Code Review)时严格把关带领新人进步。会定期通过团队内的技术分享会（比如某次解决技术难点后的分享）或编写Wiki文档将业务知识流转，遇到重复度高的直接沉淀为基础组件或者脚手架工具。而不是单打独斗。",
        "key_points": ["主动承担核心职责", "推进Code Review文化", "知识库/组件的沉淀与分享"],
        "difficulty": "medium",
        "section": "团队文化建设"
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
