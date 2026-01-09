/**
 * SheetController - FortuneSheet API 封装层
 * 提供统一的电子表格操作接口，供 AI 命令执行器调用
 */

// 获取 luckysheet 实例 (FortuneSheet 底层使用 luckysheet)
const getLuckysheet = () => {
    if (typeof window !== 'undefined' && window.luckysheet) {
        return window.luckysheet;
    }
    return null;
};

const SheetController = {
    /**
     * 设置表头样式（第一行）
     * @param {boolean} bold - 是否加粗
     * @param {string} bgColor - 背景颜色 (如 "#e8e8e8")
     */
    setHeaderStyle: (bold = true, bgColor = '#e8e8e8') => {
        const sheet = getLuckysheet();
        if (!sheet) return { success: false, error: 'Sheet not available' };

        try {
            // 获取当前表格数据
            const data = sheet.getSheetData();
            if (!data || data.length === 0) return { success: false, error: 'No data' };

            const colCount = data[0]?.length || 0;

            // 设置第一行的样式
            for (let c = 0; c < colCount; c++) {
                // 设置加粗
                if (bold) {
                    sheet.setCellValue(0, c, { bl: 1 }, { isRefresh: false });
                }
                // 设置背景色
                if (bgColor) {
                    sheet.setCellValue(0, c, { bg: bgColor }, { isRefresh: false });
                }
            }

            sheet.refresh();
            return { success: true, message: `已设置表头样式: 加粗=${bold}, 背景色=${bgColor}` };
        } catch (e) {
            return { success: false, error: e.message };
        }
    },

    /**
     * 冻结列
     * @param {number} count - 要冻结的列数 (从左边开始)
     */
    freezeColumns: (count = 1) => {
        const sheet = getLuckysheet();
        if (!sheet) return { success: false, error: 'Sheet not available' };

        try {
            // FortuneSheet/Luckysheet 冻结 API
            sheet.setFrozen('rangeBoth', {
                range: { row_focus: 0, column_focus: count - 1 }
            });
            return { success: true, message: `已冻结前 ${count} 列` };
        } catch (e) {
            return { success: false, error: e.message };
        }
    },

    /**
     * 冻结行
     * @param {number} count - 要冻结的行数 (从顶部开始)
     */
    freezeRows: (count = 1) => {
        const sheet = getLuckysheet();
        if (!sheet) return { success: false, error: 'Sheet not available' };

        try {
            sheet.setFrozen('rangeRow', {
                range: { row_focus: count - 1, column_focus: 0 }
            });
            return { success: true, message: `已冻结前 ${count} 行` };
        } catch (e) {
            return { success: false, error: e.message };
        }
    },

    /**
     * 自动调整列宽
     */
    autoFitColumnWidth: () => {
        const sheet = getLuckysheet();
        if (!sheet) return { success: false, error: 'Sheet not available' };

        try {
            const data = sheet.getSheetData();
            if (!data || data.length === 0) return { success: false, error: 'No data' };

            const colCount = data[0]?.length || 0;

            // 为每列计算最佳宽度
            for (let c = 0; c < colCount; c++) {
                let maxWidth = 50; // 最小宽度
                for (let r = 0; r < Math.min(data.length, 100); r++) {
                    const cell = data[r]?.[c];
                    const value = cell?.v || cell?.m || '';
                    const textWidth = String(value).length * 10 + 20;
                    maxWidth = Math.max(maxWidth, Math.min(textWidth, 300));
                }
                sheet.setColumnWidth([c], maxWidth);
            }

            sheet.refresh();
            return { success: true, message: '已自动调整所有列宽' };
        } catch (e) {
            return { success: false, error: e.message };
        }
    },

    /**
     * 设置条件格式
     * @param {string} columnName - 列名
     * @param {string} operator - 比较运算符 ("<", ">", "=", "contains")
     * @param {any} value - 比较值
     * @param {string} color - 满足条件时的文字颜色
     * @param {string} bgColor - 满足条件时的背景颜色
     */
    setConditionalFormat: (columnName, operator, value, color = null, bgColor = null) => {
        const sheet = getLuckysheet();
        if (!sheet) return { success: false, error: 'Sheet not available' };

        try {
            const data = sheet.getSheetData();
            if (!data || data.length === 0) return { success: false, error: 'No data' };

            // 找到列索引
            const headerRow = data[0];
            let colIndex = -1;
            for (let c = 0; c < headerRow.length; c++) {
                const cellValue = headerRow[c]?.v || headerRow[c]?.m || headerRow[c];
                if (String(cellValue) === columnName) {
                    colIndex = c;
                    break;
                }
            }

            if (colIndex === -1) {
                return { success: false, error: `找不到列: ${columnName}` };
            }

            let matchCount = 0;

            // 遍历数据行，应用条件格式
            for (let r = 1; r < data.length; r++) {
                const cell = data[r]?.[colIndex];
                const cellValue = cell?.v ?? cell?.m ?? cell;
                let matches = false;

                switch (operator) {
                    case '<':
                        matches = Number(cellValue) < Number(value);
                        break;
                    case '>':
                        matches = Number(cellValue) > Number(value);
                        break;
                    case '=':
                    case '==':
                        matches = cellValue == value;
                        break;
                    case 'contains':
                        matches = String(cellValue).includes(String(value));
                        break;
                }

                if (matches) {
                    matchCount++;
                    const style = {};
                    if (color) style.fc = color;
                    if (bgColor) style.bg = bgColor;
                    sheet.setCellValue(r, colIndex, style, { isRefresh: false });
                }
            }

            sheet.refresh();
            return { success: true, message: `已对 ${matchCount} 个单元格应用条件格式` };
        } catch (e) {
            return { success: false, error: e.message };
        }
    },

    /**
     * 设置表格边框
     * @param {string} type - 边框类型 ("outer", "inner", "all")
     * @param {string} outerStyle - 外边框样式 ("thin", "medium", "thick")
     * @param {string} innerStyle - 内边框样式 ("thin", "medium", "thick")
     */
    setBorder: (type = 'all', outerStyle = 'medium', innerStyle = 'thin') => {
        const sheet = getLuckysheet();
        if (!sheet) return { success: false, error: 'Sheet not available' };

        try {
            const data = sheet.getSheetData();
            if (!data || data.length === 0) return { success: false, error: 'No data' };

            const rowCount = data.length;
            const colCount = data[0]?.length || 0;

            // 选择整个数据区域
            sheet.setRangeShow({
                row: [0, rowCount - 1],
                column: [0, colCount - 1]
            });

            // 边框样式映射
            const styleMap = {
                thin: 1,
                medium: 2,
                thick: 3
            };

            const borderValue = {
                rangeType: 'range',
                borderType: type === 'outer' ? 'border-outside' :
                    type === 'inner' ? 'border-inside' : 'border-all',
                style: styleMap[outerStyle] || 2,
                color: '#000000'
            };

            sheet.setBorderInfo(borderValue);

            return { success: true, message: `已添加${type}边框` };
        } catch (e) {
            return { success: false, error: e.message };
        }
    },

    /**
     * 隐藏包含特定内容的行
     * @param {string} columnName - 要搜索的列名
     * @param {string} contains - 包含的文本
     */
    hideRowsWhere: (columnName, contains) => {
        const sheet = getLuckysheet();
        if (!sheet) return { success: false, error: 'Sheet not available' };

        try {
            const data = sheet.getSheetData();
            if (!data || data.length === 0) return { success: false, error: 'No data' };

            // 找到列索引
            const headerRow = data[0];
            let colIndex = -1;
            for (let c = 0; c < headerRow.length; c++) {
                const cellValue = headerRow[c]?.v || headerRow[c]?.m || headerRow[c];
                if (String(cellValue) === columnName) {
                    colIndex = c;
                    break;
                }
            }

            if (colIndex === -1) {
                return { success: false, error: `找不到列: ${columnName}` };
            }

            const rowsToHide = [];

            for (let r = 1; r < data.length; r++) {
                const cell = data[r]?.[colIndex];
                const cellValue = cell?.v ?? cell?.m ?? cell ?? '';
                if (String(cellValue).includes(contains)) {
                    rowsToHide.push(r);
                }
            }

            if (rowsToHide.length > 0) {
                sheet.hideRow(rowsToHide);
            }

            return { success: true, message: `已隐藏 ${rowsToHide.length} 行包含"${contains}"的数据` };
        } catch (e) {
            return { success: false, error: e.message };
        }
    },

    /**
     * 显示所有隐藏的行
     */
    showAllRows: () => {
        const sheet = getLuckysheet();
        if (!sheet) return { success: false, error: 'Sheet not available' };

        try {
            const data = sheet.getSheetData();
            const allRows = Array.from({ length: data.length }, (_, i) => i);
            sheet.showRow(allRows);
            return { success: true, message: '已显示所有行' };
        } catch (e) {
            return { success: false, error: e.message };
        }
    },

    /**
     * 按列排序
     * @param {string} columnName - 列名
     * @param {boolean} ascending - 是否升序
     */
    sortByColumn: (columnName, ascending = true) => {
        const sheet = getLuckysheet();
        if (!sheet) return { success: false, error: 'Sheet not available' };

        try {
            const data = sheet.getSheetData();
            if (!data || data.length === 0) return { success: false, error: 'No data' };

            // 找到列索引
            const headerRow = data[0];
            let colIndex = -1;
            for (let c = 0; c < headerRow.length; c++) {
                const cellValue = headerRow[c]?.v || headerRow[c]?.m || headerRow[c];
                if (String(cellValue) === columnName) {
                    colIndex = c;
                    break;
                }
            }

            if (colIndex === -1) {
                return { success: false, error: `找不到列: ${columnName}` };
            }

            // 选择整个数据区域（不包括表头）
            sheet.setRangeShow({
                row: [1, data.length - 1],
                column: [0, (data[0]?.length || 1) - 1]
            });

            // 执行排序
            sheet.orderByRow({
                col: colIndex,
                isAsc: ascending
            });

            return { success: true, message: `已按"${columnName}"${ascending ? '升序' : '降序'}排序` };
        } catch (e) {
            return { success: false, error: e.message };
        }
    }
};

// 导出给全局使用
if (typeof window !== 'undefined') {
    window.SheetController = SheetController;
}

export default SheetController;
