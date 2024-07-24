# 基于Quecpython的简易DTU

## 项目简介

本项目是一个基于Quecpython的简易数据传输单元（DTU），修改自Quectel的原始版本。
该DTU使用MQTT协议，通过阿里云平台进行数据传输，开发板MCU为EC600E，串口通信方式为UART。
后续版本计划在此基础上使用Modbus-RTU协议作为南向协议，以完善对DTU子设备的消息分发。

## 功能特性

- **MQTT协议**：实现数据上传至阿里云平台。
- **UART通信**：使用串口与设备进行通信。
- **Modbus-RTU协议**（计划中）：用于子设备的消息分发和管理。

## 安装与使用

### 前置条件

- 开发板：EC600E
- 云平台：阿里云
- 开发环境：Quecpython
