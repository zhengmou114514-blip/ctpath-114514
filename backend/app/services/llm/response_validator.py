"""
LLM响应验证器

验证LLM响应的格式、内容和安全性
"""

import json
import re
from typing import Dict, List, Optional, Tuple


class ValidationResult:
    """验证结果"""

    def __init__(
        self,
        is_valid: bool,
        data: Optional[Dict] = None,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None
    ):
        self.is_valid = is_valid
        self.data = data or {}
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, error: str):
        """添加错误"""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str):
        """添加警告"""
        self.warnings.append(warning)


class LLMResponseValidator:
    """
    LLM响应验证器

    验证响应的格式、内容和安全性
    """

    def __init__(self):
        """初始化验证器"""
        # 必需字段
        self.required_fields = ['risk_summary', 'care_plan', 'follow_up']

        # 敏感信息模式
        self.sensitive_patterns = [
            r'\b\d{11}\b',  # 手机号
            r'\b\d{18}\b',  # 身份证号
            r'\b[\w\.-]+@[\w\.-]+\.\w+\b',  # 邮箱
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # 银行卡
        ]

        # 禁止内容模式
        self.forbidden_patterns = [
            r'自杀',
            r'自残',
            r'放弃治疗',
            r'停止用药',
        ]

    def validate(self, response_text: str) -> ValidationResult:
        """
        验证LLM响应

        Args:
            response_text: LLM响应文本

        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)

        # 1. JSON格式验证
        parsed_data = self._validate_json_format(response_text, result)
        if not parsed_data:
            return result

        # 2. 必需字段验证
        self._validate_required_fields(parsed_data, result)

        # 3. 内容安全验证
        self._validate_content_safety(parsed_data, result)

        # 4. 敏感信息检测
        self._detect_sensitive_info(parsed_data, result)

        # 5. 内容质量验证
        self._validate_content_quality(parsed_data, result)

        if result.is_valid:
            result.data = parsed_data

        return result

    def _validate_json_format(
        self,
        response_text: str,
        result: ValidationResult
    ) -> Optional[Dict]:
        """验证JSON格式"""
        try:
            data = json.loads(response_text)
            return data
        except json.JSONDecodeError as e:
            # 尝试提取JSON
            extracted = self._extract_json(response_text)
            if extracted:
                result.add_warning(f"响应包含非JSON内容，已自动提取JSON部分")
                return extracted
            else:
                result.add_error(f"JSON格式错误: {str(e)}")
                return None

    def _extract_json(self, text: str) -> Optional[Dict]:
        """从文本中提取JSON"""
        # 查找JSON对象
        start = text.find('{')
        end = text.rfind('}')

        if start == -1 or end == -1 or end <= start:
            return None

        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            return None

    def _validate_required_fields(self, data: Dict, result: ValidationResult):
        """验证必需字段"""
        for field in self.required_fields:
            if field not in data:
                result.add_error(f"缺少必需字段: {field}")

    def _validate_content_safety(self, data: Dict, result: ValidationResult):
        """验证内容安全性"""
        def check_text(text: str, path: str):
            if not isinstance(text, str):
                return

            # 检查禁止内容
            for pattern in self.forbidden_patterns:
                if re.search(pattern, text):
                    result.add_error(f"内容包含禁止词汇: {path}")

        def check_value(value, path: str):
            if isinstance(value, str):
                check_text(value, path)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    check_value(item, f"{path}[{i}]")
            elif isinstance(value, dict):
                for k, v in value.items():
                    check_value(v, f"{path}.{k}")

        for key, value in data.items():
            check_value(value, key)

    def _detect_sensitive_info(self, data: Dict, result: ValidationResult):
        """检测敏感信息"""
        def check_text(text: str, path: str) -> bool:
            if not isinstance(text, str):
                return False

            for pattern in self.sensitive_patterns:
                if re.search(pattern, text):
                    result.add_warning(f"检测到可能的敏感信息: {path}")
                    return True
            return False

        def check_value(value, path: str) -> bool:
            if isinstance(value, str):
                return check_text(value, path)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if check_value(item, f"{path}[{i}]"):
                        return True
            elif isinstance(value, dict):
                for k, v in value.items():
                    if check_value(v, f"{path}.{k}"):
                        return True
            return False

        for key, value in data.items():
            check_value(value, key)

    def _validate_content_quality(self, data: Dict, result: ValidationResult):
        """验证内容质量"""
        total_items = 0
        empty_items = 0

        for field in self.required_fields:
            value = data.get(field)

            if isinstance(value, list):
                total_items += len(value)
                empty_items += sum(1 for item in value if not item or (isinstance(item, str) and not item.strip()))
            elif isinstance(value, str):
                total_items += 1
                if not value.strip():
                    empty_items += 1

        if total_items == 0:
            result.add_error("响应不包含任何有效建议")
        elif empty_items == total_items:
            result.add_error("所有建议字段均为空")
        elif empty_items > 0:
            result.add_warning(f"部分建议字段为空: {empty_items}/{total_items}")

    def sanitize_response(self, data: Dict) -> Dict:
        """
        清理响应数据

        Args:
            data: 原始数据

        Returns:
            Dict: 清理后的数据
        """
        sanitized = {}

        for field in self.required_fields:
            value = data.get(field)

            if isinstance(value, list):
                # 过滤空项
                sanitized[field] = [
                    self._sanitize_text(item)
                    for item in value
                    if item and (isinstance(item, str) and item.strip())
                ]
            elif isinstance(value, str):
                sanitized[field] = self._sanitize_text(value)
            else:
                sanitized[field] = []

        return sanitized

    def _sanitize_text(self, text: str) -> str:
        """清理文本"""
        # 移除敏感信息
        for pattern in self.sensitive_patterns:
            text = re.sub(pattern, '[已脱敏]', text)

        # 移除多余空白
        text = ' '.join(text.split())

        return text.strip()
