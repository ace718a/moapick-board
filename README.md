# MOAPICK Board

## 콘텐츠 게시 전 검수

새 콘텐츠를 추가하거나 수정한 뒤 `python scripts/qa_content.py`를 실행합니다. CTA 앵커와 실제 `href`, 서비스별 `moapick.co.kr` 랜딩 경로, 빈 관련정보 영역, 잘못 닫힌 HTML을 검사합니다. 자동 검사 통과 후 데스크톱과 모바일 실제 렌더링에서 카드·콜아웃·소제목 간격, overflow와 CTA 클릭 목적지를 확인합니다.

`https://board.moapick.co.kr/`용 정적 게시판입니다.

## Cloudflare Pages

- Framework preset: None
- Build command: 비워 둠
- Build output directory: `/`
- Custom domain: `board.moapick.co.kr`

현재 메인 페이지만 색인 대상으로 구성했습니다. 업종별 게시판은 실제 첫 글을 추가할 때 생성합니다.
