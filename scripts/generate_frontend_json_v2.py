import json
import os

base_dir = os.path.join(os.path.dirname(__file__), '../knowledge-base/web-frontend/questions')
os.makedirs(base_dir, exist_ok=True)

technical = []

# JS Questions
for i, (q, a, p, sec, diff) in enumerate([
    ("什么是闭包(Closure)？它有哪些优缺点？", "闭包是指函数可以记住并访问其词法作用域中的变量...优点是可以创建私有变量，缺点是常驻内存，容易导致内存泄漏。", ["词法作用域", "私有变量", "内存泄漏"], "JavaScript基础", "medium"),
    ("防抖（Debounce）和节流（Throttle）的区别及应用场景？", "防抖是指在规定时间内多次触发只执行最后一次；节流是指在规定时间内只执行一次。防抖适用于搜索框输入，节流适用于滚动条监听。", ["执行时机差别", "应用场景", "性能优化"], "JavaScript基础", "medium"),
    ("简述JS的事件循环(Event Loop)机制以及宏任务、微任务的区别？", "JS是单线程的，通过事件循环实现异步。执行过程：宏任务 -> 清空微任务队列 -> 渲染 -> 宏任务。微任务包括Promise.then，宏任务包括setTimeout。", ["单线程", "宏任务(setTimeout)", "微任务(Promise)"], "JavaScript基础", "hard"),
    ("什么是原型和原型链？", "每一个JS对象都有一个__proto__属性指向它的原型对象；当访问对象的属性时，如果找不到就会顺着__proto__向上查找，这就构成了原型链，一直到null为止。", ["__proto__", "prototype", "继承机制", "查找机制"], "JavaScript基础", "medium"),
    ("JS中this的指向规则有哪些？", "this的指向取决于函数的调用方式。1. 默认绑定（严格模式下为undefined，非严格模式下指向window）；2. 隐式绑定（谁调用就指向谁，obj.fn()指向obj）；3. 显式绑定（call, apply, bind）；4. new绑定（指向新创建的实例对象）；5. 箭头函数的this由外层词法作用域决定，不可更改。", ["默认绑定", "隐式/显式绑定", "new绑定", "箭头函数的词法作用域"], "JavaScript基础", "medium"),
    ("解释深拷贝与浅拷贝的区别，如果手写一个深拷贝如何实现？", "浅拷贝只复制一层对象属性，包含引用类型的地址。深拷贝会递归复制所有层级，完全互不影响。简单实现可用JSON.parse(JSON.stringify(obj))，但不支持函数和循环引用；手写通常通过递归判断类型(typeof/instanceof)，对于对象或数组创建新实例，并通过Map/WeakMap解决循环引用。", ["浅拷贝(Object.assign)", "深拷贝(JSON转序列化缺点)", "递归+WeakMap解决循环引用"], "JavaScript基础", "hard"),
    ("什么是JS的垃圾回收机制？", "JS引擎通过自动垃圾回收(GC)管理内存。常见的两种策略：1. 标记清除（Mark-and-Sweep），从根节点(Root)开始标记所有可达对象，未被标记的即为垃圾被清除；2. 引用计数（老旧IE使用，容易出现循环引用无法回收的问题）。现代引擎(V8)如采用分代回收机制，分为新生代(Scavenge算法)和老生代(标记清除+标记整理)。", ["标记清除机制", "引用计数的循环引用缺陷", "V8分代回收(新生代/老生代)"], "JavaScript基础", "hard"),
    ("Promise有哪些常见的方法？Promise.all和Promise.race的区别？", "常见方法包含：then, catch, finally。Promise.all()接收一个Promise数组，所有都成功才走then，只要有一个失败就走catch；Promise.race()也是接收数组，哪个Promise状态最先改变就返回它的结果。", ["Promise方法", "all", "race"], "ES6与异步编程", "medium"),
    ("async/await 和 Promise 的区别是什么？", "async/await 是建立在 Promise 之上的语法糖，使异步代码看起来像同步代码。使用 try/catch 捕获异常，比 Promise.then 链式调用更清晰，不用嵌套，在处理多重依赖异步流时具有更好的可读性。", ["语法糖", "可读性强(同步写法)", "try/catch处理异常"], "ES6与异步编程", "easy"),
    ("ES6 中 let、const 和 var 有什么区别？", "1. 作用域：var是函数/全局作用域，let/const 是块级作用域。2. 变量提升：var存在变量提升但初始化为undefined；let/const也有提升但处于暂时性死区(TDZ)，声明前无法访问。3. 可变性：const 声明时必须赋值且后续不可更改(若是对象则属性可改)，var/let 可多次赋值。4. 重复声明：var允许，let/const不允许。", ["块级作用域", "暂时性死区(TDZ)", "变量提升", "不可变性"], "ES6与异步编程", "easy"),
]):
    technical.append({"id": f"js_{i}", "job_type": "web-frontend", "category": "technical", "question": q, "reference_answer": a, "key_points": p, "difficulty": diff, "section": sec})

# HTML/CSS Questions
for i, (q, a, p, sec, diff) in enumerate([
    ("什么是HTML语义化？有哪些优点和常见标签？", "HTML语义化是根据内容的结构选择合适的标签（如header, nav, article）。优点：1. 代码可读性好；2. 对机器友好，有利于SEO；3. 方便特殊设备解析。", ["代码可读性", "SEO优化", "常见标签(main, section等)"], "HTML/CSS", "easy"),
    ("script标签中 defer 和 async 的区别是什么？", "两者都用于异步加载脚本。区别：async异步加载完成后立即执行，多个async脚本执行顺序不可控；defer会在DOM解析完成（DOMContentLoaded事件触发前）再执行，且保证顺序。", ["执行时机", "执行顺序"], "HTML/CSS", "medium"),
    ("重排(Reflow)和重绘(Repaint)是什么？如何进行优化？", "重排是元素的尺寸、结构变化引起重新局部或全部布局。重绘是外观改变但不影响布局时的重新绘制。重排必定引发重绘。优化：离线DOM操作、修改class而不是批量内联style、GPU加速(transform, opacity)。", ["重拍定义", "重绘定义", "优化(GPU, Fragment)"], "HTML/CSS", "medium"),
    ("请讲一下CSS盒子模型以及box-sizing属性的作用。", "盒子模型由 content(内容), padding(内边距), border(边框), margin(外边距)组成。box-sizing属性用于控制如何计算元素的总宽度。默认 content-box：width只含内容，加上padding会撑大盒子；border-box：width包含内容+padding+border，常用于自适应响应式布局防止被撑破。", ["标准盒模型", "怪异盒模型(border-box)", "宽度计算规则"], "HTML/CSS", "easy"),
    ("CSS水平垂直居中常用方案有哪些？", "1. Flex布局：display: flex; justify-content: center; align-items: center; 2. 绝对定位+transform：位置50%，并 translate(-50%, -50%); 3. 绝对定位+margin auto：宽高设定后，top/left/right/bottom全为0通过margin auto居中; 4. Grid布局：display: grid; place-items: center;", ["Flexbox", "Absolute+Transform", "Absolute+margin:auto"], "HTML/CSS", "medium"),
    ("谈谈BFC(块级格式化上下文)及触发条件", "BFC是一个独立的渲染区域...触发条件：根元素、float不为none、position为absolute或fixed、overflow不为visible、display为flex/flow-root。用于清除浮动、解决margin合并。", ["BFC概念", "触发条件", "解决的高度塌陷和重叠"], "HTML/CSS", "hard"),
    ("CSS选择器优先级是如何计算的？", "规则为：!important > 内联样式(style) > ID选择器 > 类/伪类/属性选择器 > 标签/伪元素选择器。具体可看作 (a, b, c, d) 四个层级累加但不会进位，优先级相同则后声明覆盖前声明。通用选择器(*)和继承属性权重为0。", ["优先级顺序(!important, id, class)", "权值不进位机制"], "HTML/CSS", "easy"),
]):
    technical.append({"id": f"css_{i}", "job_type": "web-frontend", "category": "technical", "question": q, "reference_answer": a, "key_points": p, "difficulty": diff, "section": sec})

# Framework & Engineering
for i, (q, a, p, sec, diff) in enumerate([
    ("简述Vue的双向数据绑定原理（Vue2与Vue3的差异）？", "Vue2基于 Object.defineProperty 进行数据劫持结合发布订阅模式（Dep/Watcher），无法监听对象属性的新增和数组索引修改。Vue3使用 Proxy 进行代理结合Reflect操作对象，性能更好，支持深度动态代理。", ["Vue2 defineProperty缺点", "Vue3 Proxy+Reflect优势", "发布订阅/依赖收集"], "Vue框架", "hard"),
    ("什么是虚拟DOM(Virtual DOM)？为什么要使用它？", "虚拟DOM是用JS对象模拟真实的DOM树结构和属性。每次状态更新时，框架会生成新的虚拟DOM，与旧的进行Diff算法对比，将所有的差异收集起来再批量更新到真实DOM上。它提升了DOM频繁操作的效率并赋予了跨平台能力(RN/Weex)。", ["JS对象抽象DOM", "Diff算法比较批量更新", "跨平台能力"], "Vue/React核心原理", "medium"),
    ("在React中，useEffect的依赖数组有几种情况？", "1. 不传：每次重新渲染都执行；2. 空数组[]：仅挂载和卸载时执行；3. 有值[a,b]：初始化以及数组内依赖项发生变化时才执行。", ["不传", "空数组", "有具体依赖变动"], "React框架", "easy"),
    ("React的Fiber架构是什么？解决了什么问题？", "Fiber是React 16引入的全新底层协调引擎。之前React从头到尾同步比对DOM树(Stack Reconciler)，当层级很深时会长时间占据浏览器主线程导致动画卡顿和输入延迟。Fiber将大任务拆分为多个可中断的小任务分片(Time Slicing/时间切片)，并且可以根据优先级让出主线程给高优任务(如用户交互)。", ["解决主线程阻塞卡顿", "时间切片(Time Slicing)", "可中断和恢复"], "React框架", "hard"),
    ("Vue组件间的通信方式有哪些？", "1. props / $emit (父子)；2. provide / inject (祖孙跨层级)；3. EventBus (Vue2，通过挂载全局Vue实例)；4. Vuex / Pinia (状态管理库)；5. ref/$refs 直接获取子组件实例操作；6. $attrs / $listeners (非props属性透传)。", ["props/$emit", "Pinia/Vuex全局", "provide/inject"], "Vue框架", "medium"),
    ("Webpack中loader和plugin的区别是什么？", "Loader本质上是转换器，Webpack只认识JS/JSON，Loader将非纯JS文件（如SCSS/TS）转化为支持的模块。Plugin是插件，在Webpack构建周期的广播事件树中注入特定的构建行为，如代码压缩(Terser)、分包(SplitChunks)、提取CSS等。", ["Loader预处理器或转换器", "Plugin钩在生命周期扩展功能"], "前端工程化", "medium"),
    ("前端前端跨域的解决方案有哪些？", "1. CORS：后端配置跨域资源共享相关Header；2. JSONP：利用script标签请求跨域但仅限GET；3. Nginx反向代理或Node中间件：服务器之间没有同源策略；4. postMessage处理iframe内跨域；5. WebSocket双向通信支持跨域。", ["CORS", "Nginx反代", "JSONP及缺点"], "计算机网络", "medium"),
    ("TCP三次握手和四次挥手的过程？为什么不是两次？", "三次握手(SYN -> SYN+ACK -> ACK)用于确认信道双向可达。如果是两次握手，服务端回复即确认并分配资源，若客户端之前的延迟SYN突然到达，服务端会白白浪费资源建立历史无效连接。四次挥手为了实现全双工下的分别断开半关闭状态(FIN -> ACK，等待数据发完，再发FIN -> ACK)。", ["双向确认机制", "防止历史滞留SYN引起资源浪费", "半关闭状态等待数据收发结束"], "计算机网络", "hard"),
]):
    technical.append({"id": f"fw_{i}", "job_type": "web-frontend", "category": "technical", "question": q, "reference_answer": a, "key_points": p, "difficulty": diff, "section": sec})

scenarios = []
for i, (q, a, p, sec, diff) in enumerate([
    ("如果后端一次性返回10万条数据，前端如何渲染不卡顿？", "直接渲染10万个节点会卡死主线程引发重排。方案：1. 虚拟列表(Virtual List)动态渲染可视区域内的DOM及少许缓冲区节点以提高性能；2. 结合requestAnimationFrame与DocumentFragment分批次慢慢插入离线DOM；3. 根据业务要求，和后端协商要求转为分页或瀑布流懒加载。", ["虚拟列表计算视口", "时间切片/分批插入", "推翻协商分页"], "大厂场景题", "hard"),
    ("首屏加载白屏时间过长，你是如何分析和优化的？", "1. 利用Chrome Performance与Network面板或Lighthouse定位瓶颈。2. 优化体积：代码切割(路由懒加载)、Gzip/Brotli压缩、Terser压缩、抽出强依赖进入SplitChunks或CDN。3. 优化网络和资源：HTTP/2多路复用，骨架屏过渡。4. 引入SSR(服务端渲染)直出HTML提升FCP体验。", ["分析指标FCP/LCP", "资源打包与路由懒加载", "网络协议优化与CDN部署"], "性能优化排查", "hard"),
    ("多个请求并发获取数据，如何实现请求的“并发控制”（例如最多同时发送3个请求）？", "实现一个并发控制器：维护内部计数器(正在执行数量)和等待任务队列数组。遍历执行达到并发上限后则等待；只要一个Promise状态落定(.finally内)，计数器减1并将等待队列中的下一个任务Shift()出来继续发送。这能在防住服务器峰值压力的同时最大化并发速度。", ["维护并发池和等待队列", "控制并发上限机制", "递归执行与边界控制"], "网络与异步并发", "hard"),
    ("线上监控显示有大量内存泄漏，怎么排查和处理？", "复现现象后用Chrome DevTools的Memory面板获取Heap Snapshot(堆快照)，找出Detached DOM(悬空DOM对象)。通常原因排查：1. 闭包引用的大型对象迟迟不释放；2. 频繁创建和未被clearInterval清理的定时器；3. Vue/React组件销毁前，绑定的window/document全局事件未被removeEventListener处理。修复就是在对应生命周期钩子里执行清理。", ["Memory堆快照排查", "清理闭包和定时器", "在beforeDestroy卸载全局事件"], "线上排查", "hard"),
]):
    scenarios.append({"id": f"scn_{i}", "job_type": "web-frontend", "category": "scenario", "question": q, "reference_answer": a, "key_points": p, "difficulty": diff, "section": sec})

projects = []
for i, (q, a, p, sec, diff) in enumerate([
    ("你在XX项目中担任了什么角色？该项目的整体前端架构是怎样的？", "【考察宏观视角】遵循STAR法则：Situation(原系统痛点)，Task(承担的核心职责)，Action(重构从选型Vue3+Vite，到模块拆分、权限配置、封装通用业务组件，搭建监控上报机制)，Result(有效支持了数百个页面的流畅运行，使得业务迭代效率提升X%)。不可只回答CRUD。", ["STAR法则", "技术选型全景图", "系统横向思考能力(架构层面)"], "项目架构", "medium"),
    ("项目中遇到的技术挑战/难点是什么？如何攻克的？", "【考察技术深度和破局能力】可讲性能优化或基建：如存在渲染大量复杂表格及动画导致的FPS极低，于是引入Web Worker做复杂计算、或利用canvas双缓冲技术渲染；或者基建方面：主导抽象私有组件库推向内部镜像仓库，整合eslint等卡点提升了整体前端团队的代码规范程度，通过对比说明提升比例。", ["客观呈现难点瓶颈", "技术论证(多种方案探讨过滤)", "可量化的业务价值提升"], "技术深度与攻坚", "hard"),
]):
    projects.append({"id": f"prj_{i}", "job_type": "web-frontend", "category": "project", "question": q, "reference_answer": a, "key_points": p, "difficulty": diff, "section": sec})

behavioral = []
for i, (q, a, p, sec, diff) in enumerate([
    ("发现后端接口设计严重不合理很难对接时，你会怎么办？", "1. 保持客观理性：不要单纯抱怨，而应具体指出如层级深或全量更新拖慢用户体验和造成大量冗余风险。2. 提改进方案：给出目前响应时间截图及期待的理想JSON聚合结构等，寻求能否修改。3. 协商妥协：如果无法改，通过在BFF层(如Node中间层)/前端封装适配器聚合接口层来兼容，必要时推进项目复盘，向上级和PM反馈不合理带来的维护成本。", ["从系统风险/体验出发", "提供解决替代方案不推诿", "寻求妥协并复盘经验"], "跨部门协作", "medium"),
    ("如果时间极其紧迫且几个任务插队，你要如何排期？", "绝不盲接或盲拒。1. 对任务做四象限评估（重要/紧急情况）并梳理当前可用资源容量。2. 和PM探讨做业务做减法，商议出MVP(最小可用产品)的敏捷分批上线方案。3. 暴露风险与协调：向主管求助临时协调额外资源。并在事后加强团队内部对“临时插队规范”和项目流程的严谨约束管理。", ["时间四象限管理", "敏捷拆解MVP方案", "暴露风险与寻求资源支援"], "项目管理", "medium"),
]):
    behavioral.append({"id": f"bhv_{i}", "job_type": "web-frontend", "category": "behavioral", "question": q, "reference_answer": a, "key_points": p, "difficulty": diff, "section": sec})

# Write to files
with open(os.path.join(base_dir, 'frontend_technical.json'), 'w', encoding='utf-8') as f:
    json.dump(technical, f, ensure_ascii=False, indent=4)

with open(os.path.join(base_dir, 'scenarios.json'), 'w', encoding='utf-8') as f:
    json.dump(scenarios, f, ensure_ascii=False, indent=4)

with open(os.path.join(base_dir, 'projects.json'), 'w', encoding='utf-8') as f:
    json.dump(projects, f, ensure_ascii=False, indent=4)

with open(os.path.join(base_dir, 'behavioral.json'), 'w', encoding='utf-8') as f:
    json.dump(behavioral, f, ensure_ascii=False, indent=4)
