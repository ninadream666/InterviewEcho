import { test, expect } from '@playwright/test'

test.describe('黄金路径回归测试 (Golden Path)', () => {
  
  test.beforeEach(async ({ page }) => {
    // 1. 智能寻路：优先尝试直接进入登录页
    await page.goto('/login', { waitUntil: 'domcontentloaded' }).catch(() => {})
    
    try {
      await page.waitForSelector('input[placeholder="请输入您的用户名"]', { timeout: 2000 })
    } catch (e) {
      // 找不到输入框？尝试 Hash 路由模式
      await page.goto('/#/login', { waitUntil: 'domcontentloaded' }).catch(() => {})
      try {
        await page.waitForSelector('input[placeholder="请输入您的用户名"]', { timeout: 2000 })
      } catch (e2) {
        // 如果还不行，回退到根目录找界面的入口按钮
        await page.goto('/', { waitUntil: 'domcontentloaded' })
        const entryBtn = page.locator('button, a').filter({ hasText: /登录|开始|体验/i }).first()
        if (await entryBtn.isVisible()) await entryBtn.click()
      }
    }

    // 终极断言：必须确保登录输入框出现
    await page.waitForSelector('input[placeholder="请输入您的用户名"]', { timeout: 10000 })
    
    // 2. 检查是否在登录模式，若是则切到注册模式
    const toRegisterBtn = page.locator('button', { hasText: '没有账号？创建新账号' })
    if (await toRegisterBtn.isVisible()) {
      await toRegisterBtn.click()
    }
    
    // 3. 注册全新随机账号
    const testUser = `golden_e2e_${Date.now()}`
    await page.getByPlaceholder('请输入您的用户名').fill(testUser)
    await page.getByPlaceholder('请输入密码').fill('password123')
    
    await page.locator('button', { hasText: '注 册' }).click()
    
    // 【核心修复】：不再捕捉不稳定的 ElMessage 提示框！
    // 根据 LoginView.vue 源码，注册成功后 isRegister 变为 false，标题瞬间恢复为 '欢迎回来'
    await expect(page.locator('text=欢迎回来')).toBeVisible({ timeout: 10000 })
    
    // 4. 等待界面自动切回登录模式（出现“登 录”按钮）
    const loginBtn = page.locator('button', { hasText: '登 录' })
    await expect(loginBtn).toBeVisible({ timeout: 10000 })
    
    // 强力物理防抖 1 秒钟，确保 Vue 绑定的 click 事件彻底恢复
    await page.waitForTimeout(1000) 
    
    // 执行登录
    await loginBtn.click()
    
    // 【核心修复】：直接监听最终业务结果，无视登录弹窗
    // 5. 断言成功跳转至 Dashboard
    await expect(page).toHaveURL(/.*dashboard/, { timeout: 15000 })
  })

  test('完成一场完整的普通模拟面试', async ({ page }) => {
    // 2. Dashboard - 选择岗位发起面试
    await page.locator('h3', { hasText: 'Java后端开发工程师' }).click()

    // 3. Settings Dialog - 确认配置并进入房间
    const confirmBtn = page.locator('button', { hasText: '确认配置并进入房间' })
    await expect(confirmBtn).toBeVisible()
    await confirmBtn.click()

    // 4. Interview Room - 等待房间加载和 AI 第一句开场白
    await expect(page).toHaveURL(/.*interview/, { timeout: 15000 })
    // 确保 Loading 提示消失，AI 打招呼的聊天气泡出现
    await expect(page.locator('text=正在为您协调面试官')).toBeHidden({ timeout: 15000 })
    await expect(page.locator('text=你好，我是你的Java后端')).toBeVisible({ timeout: 20000 })

    // 5. 模拟用户发送文字回答
    const chatInput = page.locator('textarea[placeholder*="请输入您的回答"]')
    await chatInput.fill('你好，面试官。我已经准备好开始面试了。')
    
    const sendBtn = page.locator('button', { hasText: '发送 (Enter)' })
    await expect(sendBtn).toBeEnabled()
    await sendBtn.click()

    // 验证发送状态和 AI 回复
    await expect(page.locator('text=发送中...')).toBeHidden({ timeout: 45000 }) // LLM 响应可能需要较长时间
    
    // 6. 模拟主动结束面试
    const endInterviewBtn = page.locator('button', { hasText: '结束面试' })
    await expect(endInterviewBtn).toBeVisible()
    await endInterviewBtn.click()

    // 7. Report View - 验证报告生成结果
    await expect(page.locator('text=正在为整场面试进行深度评估')).toBeVisible()
    await expect(page).toHaveURL(/.*report/, { timeout: 60000 }) // 评估可能需要 60s 左右
    
    // 验证报告页面的核心组件正常渲染
    await expect(page.locator('text=面试评估报告')).toBeVisible()
    await expect(page.locator('text=多维度能力图谱')).toBeVisible()
    await expect(page.locator('text=评估维度明细')).toBeVisible() 
  })
})