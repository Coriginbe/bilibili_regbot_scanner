# CHANGELOG / 更新日志

All notable changes to this project will be documented in this file.  

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).  

## [1.1.0] - 2026-07-27

### Added / 新增
- 从 `div.nav-statistics` 提取粉丝数和关注数
- 检测 `main.space-main` 区域是否存在用户发布内容
- 新增 `contains_surname()` 检测用户名中的常见姓氏
- 新增 `contains_year_or_date()` 检测用户名中的年份或日期数字格式

### Changed / 变更
- `is_gibberish_name()` 允许用户名包含数字字符，字母部分至少为4位
- `is_gibberish_name()` 用户名长度范围从 `6~12` 扩展至 `6~16`
- 命中判定从单条件（乱码名+Lv0）变更为多维度组合（乱码名+Lv0+粉丝0+关注0+无内容）
- `page.get()` 后等待时间从 `1.5s` 调整为 `2s`
- 输出日志新增粉丝数、关注数、内容状态字段

### Fixed / 修复
- 增强异常处理逻辑，提升长时间运行稳定性
