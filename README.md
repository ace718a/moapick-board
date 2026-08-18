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

## 목록 자동 페이지네이션

메인 인덱스와 `moving / rent / internet / water` 업종별 인덱스는 `scripts/build_indexes.py`가 상세페이지를 자동 스캔해 생성합니다.

- 페이지당 게시글: **10개**
- 1~10개: `/index.html`
- 11~20개: `/page/2/index.html`
- 21~30개: `/page/3/index.html`
- 업종별 목록도 동일하게 `/moving/page/2/`, `/internet/page/2/` 형태로 생성
- 게시글 수가 줄면 불필요해진 예전 `page/` 디렉터리는 자동 삭제
- 신규 상세페이지는 기존 목록에 없으면 최신 글로 인식해 1페이지 상단에 배치

로컬 수동 실행:

```bash
python scripts/build_indexes.py
python scripts/qa_content.py
```

### Cloudflare Pages 자동 실행

Cloudflare Pages의 **Build command**를 아래처럼 한 번 설정합니다.

```bash
python scripts/build_indexes.py && python scripts/qa_content.py
```

Build output directory는 기존처럼 `/`를 유지합니다.

이 설정 이후에는 상세페이지를 Git에 추가하면 배포 과정에서 메인/업종별 목록과 2·3페이지가 자동 생성됩니다.
