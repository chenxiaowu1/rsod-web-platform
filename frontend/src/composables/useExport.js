import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { exportDetection } from '../api/detection'

export function useExport() {
  const exporting = ref(false)

  async function doExport(recordId, format) {
    exporting.value = true
    try {
      const blob = await exportDetection(recordId, format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const extMap = { coco: 'json', yolo: 'txt', geojson: 'geojson' }
      a.download = `detection_${recordId.slice(0, 8)}.${extMap[format]}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      ElMessage.success(`已导出 ${format.toUpperCase()} 格式`)
    } catch (e) {
      ElMessage.error('导出失败')
    } finally {
      exporting.value = false
    }
  }

  async function batchExport(recordIds, format) {
    exporting.value = true
    try {
      const JSZip = (await import('jszip')).default
      const zip = new JSZip()
      for (const id of recordIds) {
        const blob = await exportDetection(id, format)
        const extMap = { coco: 'json', yolo: 'txt', geojson: 'geojson' }
        zip.file(`detection_${id.slice(0, 8)}.${extMap[format]}`, blob)
      }
      const zipBlob = await zip.generateAsync({ type: 'blob' })
      const url = URL.createObjectURL(zipBlob)
      const a = document.createElement('a')
      a.href = url
      a.download = `annotations_batch_${Date.now()}.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      ElMessage.success(`已导出 ${recordIds.length} 条标注`)
    } catch (e) {
      ElMessage.error('批量导出失败')
    } finally {
      exporting.value = false
    }
  }

  return { exporting, doExport, batchExport }
}
