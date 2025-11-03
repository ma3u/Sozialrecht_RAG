# SACHBEARBEITER GRAPH ANALYSIS REPORT
**Generated:** 2025-11-03 09:04:06

---

## 📋 Executive Summary for Case Workers

### Graph Coverage
- **Total Legal Norms:** 4,223
- **Available Chunks (for RAG):** 41,781
- **SGB Books:** 13
- **PDF Documents:** 50

### 🔄 Workflow Path Analysis

**UC1: Regelbedarfe (§ 20 SGB II)** ✅
- Path length: 1
- Chunks available: 96

**SGB Coverage for Case Work:**

| SGB | Structures | Norms | Chunks | Complete Path |
|-----|-----------|-------|--------|---------------|
| I | 9 | 18 | 0 | ❌ |
| II | 21 | 34 | 0 | ❌ |
| III | 107 | 300 | 0 | ❌ |
| IV | 31 | 40 | 0 | ❌ |
| IX | 44 | 44 | 0 | ❌ |
| V | 107 | 283 | 0 | ❌ |
| VI | 111 | 223 | 0 | ❌ |
| VII | 66 | 228 | 0 | ❌ |
| VIII | 39 | 178 | 0 | ❌ |
| X | 26 | 95 | 0 | ❌ |
| XI | 61 | 202 | 0 | ❌ |
| XII | 42 | 186 | 0 | ❌ |
| XIV | 53 | 66 | 0 | ❌ |

### ⚠️ Issues Affecting Case Work

**Norms Without RAG Chunks:**
- SGB III: 444 norms missing chunks
- SGB V: 422 norms missing chunks
- SGB VI: 364 norms missing chunks
- SGB VII: 312 norms missing chunks
- SGB XI: 268 norms missing chunks

## 💡 Recommendations for Sachbearbeiter

1. **Primary Sources:** Use SGBs with complete paths (✅ in table above)
2. **Backup Strategy:** For SGBs without chunks, use direct text queries
3. **Verify Amendments:** Check `amendment_date` for recent changes
4. **Cross-SGB Cases:** Path analysis shows all 13 SGBs are available
