from pathlib import Path

import cv2

from target_detection import detect_target


# 대표 프레임의 검출 결과에 경계 사각형과 중심점을 그려 저장한다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 356번은 Run 시작과 최초 ON_TARGET을 함께 확인하는 대표 프레임이다.
FRAME_PATH = PROJECT_ROOT / "outputs" / "representative_frame_356.png"
DETECTION_OUTPUT_PATH = PROJECT_ROOT / "outputs" / "target_detection_356.png"


def main() -> None:
    # 대표 프레임이 없으면 선행 스크립트의 실행 순서를 안내한다.
    if not FRAME_PATH.exists():
        raise FileNotFoundError(
            "대표 프레임이 없습니다. inspect_target_frame.py를 먼저 실행하세요: "
            f"{FRAME_PATH}"
        )
    if not FRAME_PATH.is_file():
        raise ValueError(f"대표 프레임 경로가 파일이 아닙니다: {FRAME_PATH}")

    frame = cv2.imread(str(FRAME_PATH))

    if frame is None:
        raise ValueError(f"대표 프레임 이미지를 읽을 수 없습니다: {FRAME_PATH}")

    # 공용 검출 함수를 호출해 후보 개수와 단일 타겟 위치를 얻는다.
    (
        target_detected,
        bounding_box,
        center,
        contour_count,
        valid_candidate_count,
        selected_contour,
    ) = detect_target(frame)

    print(f"전체 윤곽선 후보 수: {contour_count}")
    print(f"면적 필터를 통과한 후보 수: {valid_candidate_count}")
    print(f"타겟 검출 여부: {target_detected}")

    # 선택된 외곽선을 출력해 실제 검출 형태를 확인한다.
    if selected_contour is not None:
        print(f"타겟의 테두리 값 {selected_contour}")
    else:
        print(f"타겟의 테두리 값이 존재하지 않습니다.")

    if not target_detected:
        if valid_candidate_count == 0:
            print("면적 필터를 통과한 타겟 후보가 없습니다.")
        else:
            print(
                "유효 타겟을 하나로 결정할 수 없습니다: "
                f"유효 후보 수={valid_candidate_count}"
            )
        return

    if bounding_box is None or center is None:
        raise RuntimeError("타겟 검출 결과의 경계 사각형 또는 중심 좌표가 없습니다.")

    # 선택된 Contour, 경계 사각형, 타겟 중심을 원본 위에 표시한다.
    x, y, width, height = bounding_box
    center_x, center_y = center

    print(
        "타겟 검출 결과 | "
        f"경계 사각형=(x={x}, y={y}, 너비={width}, 높이={height}) | "
        f"중심 좌표=({center_x}, {center_y})"
    )

    visualized_frame = frame.copy()

    # 노란색 1px 선으로 사각형과 실제 타겟 외곽의 차이를 본다.
    cv2.drawContours(
        visualized_frame,
        [selected_contour],
        0,
        (0, 255, 255),
        1,
    )

    # 초록색 사각형도 1px로 그려 경계 픽셀을 가리지 않는다.
    top_left = (x, y)
    bottom_right = (
        x + width - 1,
        y + height - 1,
    )

    cv2.rectangle(
        visualized_frame,
        top_left,
        bottom_right,
        (0, 255, 0),
        1,
    )

    # 빨간 점은 Target 중심이며 Screen Center Crosshair와는 다르다.
    center_point = (
        round(center_x),
        round(center_y),
    )

    cv2.circle(
        visualized_frame,
        center_point,
        5,
        (0, 0, 255),
        -1,
    )

    # 고정된 파일명으로 저장해 재실행 시 이미지가 계속 누적되지 않게 한다.
    DETECTION_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    visualization_save_success = cv2.imwrite(
        str(DETECTION_OUTPUT_PATH),
        visualized_frame,
    )

    if not visualization_save_success:
        raise RuntimeError(
            f"타겟 검출 시각화 이미지를 저장하지 못했습니다: "
            f"{DETECTION_OUTPUT_PATH}"
        )

    print(f"타겟 검출 시각화 저장 경로: {DETECTION_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
