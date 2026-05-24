import { ElMessage } from 'element-plus'

export function useChatExport() {
  function exportMarkdown(session) {
    const lines = [
      `# ${session.title}`,
      `> ${new Date().toLocaleString()}`,
      '',
    ]
    for (const msg of session.messages) {
      const role = msg.role === 'user' ? '**用户**' : '**AI 助手**'
      lines.push(`### ${role}`, '', msg.content, '')
    }
    const blob = new Blob([lines.join('\n')], { type: 'text/markdown' })
    downloadBlob(blob, `${session.title || '对话'}.md`)
    ElMessage.success('已导出 Markdown')
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return { exportMarkdown }
}
