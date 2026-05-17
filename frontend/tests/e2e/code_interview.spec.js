import { test, expect } from '@playwright/test'

test.describe('代码面试交互测试 (Code Mode)', () => {
  
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
    const testUser = `code_e2e_${Date.now()}`
    await page.getByPlaceholder('请输入您的用户名').fill(testUser)
    await page.getByPlaceholder('请输入密码').fill('password123')
    
    await page.locator('button', { hasText: '注 册' }).click()
    
    // 【核心修复】：同上，等待 isRegister 变为 false 页面出现 '欢迎回来'
    await expect(page.locator('text=欢迎回来')).toBeVisible({ timeout: 10000 })
    
    // 4. 等待界面自动切回登录模式（出现“登 录”按钮）
    const loginBtn = page.locator('button', { hasText: '登 录' })
    await expect(loginBtn).toBeVisible({ timeout: 10000 })
    
    // 强力物理防抖 1 秒钟
    await page.waitForTimeout(1000) 
    
    // 执行登录
    await loginBtn.click()
    
    // 5. 断言成功跳转至 Dashboard
    await expect(page).toHaveURL(/.*dashboard/, { timeout: 15000 })
  })

  test('验证代码模式分屏及动态超时重置', async ({ page }) => {
    // 发起 Python 算法岗面试
    await page.locator('h3', { hasText: 'Python算法工程师' }).click()
    await page.locator('button', { hasText: '确认配置并进入房间' }).click()
    await expect(page).toHaveURL(/.*interview/, { timeout: 15000 })

    // 等待 AI 开场
    await expect(page.locator('text=正在为您协调面试官')).toBeHidden({ timeout: 15000 })
    await expect(page.locator('text=你好，我是你的Python算法')).toBeVisible({ timeout: 20000 })

    // 验证默认超时倒计时
    const timerDisplay = page.locator('text=剩余回答时间').locator('..') // 获取父节点
    await expect(timerDisplay).toContainText(/0:5\d/) 

    // 开启代码面试模式
    await page.locator('button', { hasText: '代码面试模式' }).click()

    // 验证右侧 CodeEditor 组件是否成功渲染
    await expect(page.locator('text=代码编辑器')).toBeVisible()
    await expect(page.locator('button', { hasText: '重置代码' })).toBeVisible()

    // 验证超时倒计时是否动态重置为了 30 分钟
    await expect(timerDisplay).toContainText(/30:00|29:5\d/)

    // 模拟提交代码动作
    await page.locator('button', { hasText: '提交代码给面试官' }).click()

    // 验证气泡流中是否成功追加了包含代码片段格式的对话记录
    await expect(page.locator('text=我完成了代码编写（语言：python）')).toBeVisible()
    
    // 验证 AI 面试官成功进入思考/打字状态
    await expect(page.locator('text=发送中...')).toBeVisible()

    // 等待 AI 回复完毕
    await expect(page.locator('text=发送中...')).toBeHidden({ timeout: 45000 })

    // 点击顶部栏的结束面试按钮
    const endBtn = page.locator('button', { hasText: '结束面试' })
    await expect(endBtn).toBeVisible()
    await endBtn.click()

    // 验证触发了后端评估并成功跳转至报告页
    await expect(page.locator('text=正在为整场面试进行深度评估')).toBeVisible()
    await expect(page).toHaveURL(/.*report/, { timeout: 60000 })
  })
})