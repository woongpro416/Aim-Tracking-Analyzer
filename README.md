# Vision-based Aim Tracking Analyzer

에임 트레이너의 플레이 영상을 분석해, 움직이는 타겟을 따라가는 조준 과정을 살펴보는 프로젝트입니다. 게임 점수만으로 파악하기 어려운 조준 상태의 변화를 영상에서 확인하는 것을 목표로 합니다.

## 1. 프로젝트 개요

- 프로젝트명: Vision-based Aim Tracking Analyzer
- 개발 형태: 개인 포트폴리오 프로젝트, AI-assisted development
- 도메인: Aim Trainer 녹화 영상의 Target 검출 및 Tracking State 분석
- 구조: Python, OpenCV, NumPy 기반 로컬 영상 분석 스크립트
- 현재 진행 상태: 영상 분석 코어와 검출 비교 기능까지 구현했으며, 최종 검출 정책을 검토 중
- 저장소:

## 2. 주요 기능

- 영상 파일 경로, Video Open, FPS·해상도 메타데이터 검증
- 영상 순차 디코딩과 사람이 확인한 시작 시각 기준의 60초 Run 구간 처리
- HSV Mask와 Contour 면적 조건을 이용한 청록색 Target 후보 검출
- 유효 후보가 정확히 하나일 때 Bounding Box, Center, Contour 선택
- 화면 중앙점과 Target Contour의 관계로 ON_TARGET / OFF_TARGET / MISSING 분류
- Raw Target Observation과 Tracking State Sequence 기록, 상태 Count·Frame 수 정합성 확인
- 최초 ON_TARGET Frame과 초기 확보 구간의 시간 경계 계산
- 대표 Frame 추출, 픽셀·Contour 검사 및 Mask 이미지 저장
- 별도 검사 스크립트에서 검출 방식 비교와 후보 형상값 관찰

## 3. 담당 역할

- 영상 입력 검증, 순차 디코딩, Frame 시간과 Run 구간 처리 로직 직접 구현
- HSV Mask, Contour 후보, Bounding Box와 Center 계산 흐름을 작성하고 원본 Frame으로 확인
- Contour 기반 상태 분류, 상태별 Count, 최초 ON_TARGET 경계 구현
- 대표 Frame을 직접 확인하고 검출 결과와 상태를 수동 판단
- AI 도움으로 개념 설명과 코드 Review, 일부 공통 함수·검출 비교 코드 수정 및 문서 정리 진행

## 4. 기술 스택

| 영역 | 기술 | 역할 |
| --- | --- | --- |
| 분석 코어 | Python | 영상 처리 흐름, 함수, 관찰값과 상태 기록 |
| Computer Vision | OpenCV | 영상 디코딩, HSV Mask, Contour, Point-in-Contour, Closing 실험 |
| 배열 처리 | NumPy | 이미지 배열, 자료형, Morphology Kernel |
| 테스트 | pytest | 검출·상태·후보 필터·비교 함수의 합성 테스트 |
| 파일 / 출력 | pathlib, math, pprint | 파일 경로, 수치 검증·원형도 계산, Dictionary 출력 |
| 문서 | Markdown, Mermaid | 요구사항, 작업 기록, 분석 흐름 설명 |

## 5. 시스템 아키텍처


## 6. ERD

## 7. API 명세

## 8. 실행 방법


## 9. 테스트 / 검증 방법

## 10. 트러블슈팅

## 11. 배포 / 링크

## 12. 한계와 개선 방향
