"""共享枚举定义"""

from enum import Enum


class UserRole(str, Enum):
    """用户角色"""
    ROOT = "root"        # 管理员 - 可以创建账号、管理所有数据
    TESTER = "tester"    # 测试人员 - 可以参与评测和评审


class ExperimentStatus(str, Enum):
    """实验状态"""
    DRAFT = "draft"          # 草稿
    RUNNING = "running"      # 进行中
    COMPLETED = "completed"  # 已完成
    ARCHIVED = "archived"    # 已归档


class GroupStatus(str, Enum):
    """实验组状态"""
    PENDING = "pending"                  # 待评测
    OBJECTIVE_PASS = "objective_pass"    # 客观指标通过
    OBJECTIVE_FAIL = "objective_fail"    # 客观指标未通过
    SUBJECTIVE_PASS = "subjective_pass"  # 主观评测通过
    SUBJECTIVE_FAIL = "subjective_fail"  # 主观评测未通过
    ONLINE = "online"                    # 已上线
    REJECTED = "rejected"                # 已驳回


class ReferenceType(str, Enum):
    """参考类型"""
    SUPPLIER = "supplier"  # 对齐其他供应商
    SELF = "self"          # 自对齐(降低码率)
    NEW = "new"            # 全新模板


class EvaluationType(str, Enum):
    """评测类型"""
    STATIC_FRAME = "static_frame"  # 静帧评测
    BLIND_TEST = "blind_test"      # 盲测


class ReviewResult(str, Enum):
    """评审结果"""
    PENDING = "pending"  # 待评审
    PASS = "pass"        # 通过
    REJECT = "reject"    # 驳回


class IssueType(str, Enum):
    """问题类型 (截图标注)"""
    BLUR = "blur"              # 模糊
    MOSAIC = "mosaic"          # 马赛克
    RINGING = "ringing"        # 振铃效应
    ARTIFACT = "artifact"      # 伪影
    COLOR_LOSS = "color_loss"  # 色彩失真
    CONTOUR = "contour"        # 轮廓缺失
    MOTION = "motion"          # 拖影
    OTHER = "other"            # 其他
