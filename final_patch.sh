<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>해솔7 지킴이 — 홈</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root { --haesol-green: #1a7a4a; --haesol-light: #e8f5ee; }
    body { background: #f4f6f8; margin: 0; padding: 0; }
    .navbar { background: var(--haesol-green) !important; }
    .navbar-brand { color: #fff !important; font-size: 1.2rem; }
    .nav-link { color: rgba(255,255,255,0.85) !important; }
    .nav-link:hover, .nav-link.active { color: #fff !important; }
    .nav-link.chat-link { background: rgba(255,255,255,0.15); border-radius: 8px; padding: 4px 12px !important; }
    .nav-link.chat-link:hover { background: rgba(255,255,255,0.25); }
    .noti-badge { font-size: 0.55rem; min-width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; }
  </style>
  
<style>
  :root { --g: #1a7a4a; --gl: #e8f5ee; --gb: #a8d5b8; }
  body { background: #f0f2f5; }

  .layout {
    display: grid;
    grid-template-columns: 200px 1fr 210px;
    gap: 10px;
    height: calc(100vh - 58px);
    padding: 10px;
  }
  @media (max-width: 991px) {
    .layout { grid-template-columns: 1fr; height: auto; }
    .panel-left, .panel-right { display: none; }
  }

  .panel { background: #fff; border-radius: 14px; border: 1px solid #e4e6ea; display: flex; flex-direction: column; overflow: hidden; }
  .ph { padding: 11px 13px; border-bottom: 1px solid #f0f2f4; background: #fafbfc; flex-shrink: 0; }
  .ph-title { font-size: 0.82rem; font-weight: 700; color: #333; margin: 0; }
  .pb { flex: 1; overflow-y: auto; padding: 10px; }
  .pb::-webkit-scrollbar { width: 3px; }
  .pb::-webkit-scrollbar-thumb { background: #ddd; border-radius: 3px; }

  /* 채팅 탭 드롭다운 */
  .chat-tab-bar { padding: 8px 10px; background: #fafbfc; border-bottom: 1px solid #f0f2f4; display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
  .tab-dropdown { position: relative; }
  .tab-dropdown-btn {
    display: flex; align-items: center; gap: 6px;
    padding: 6px 12px; border-radius: 20px;
    background: var(--g); color: #fff; border: none;
    font-size: 0.8rem; font-weight: 600; cursor: pointer;
    transition: opacity .15s;
  }
  .tab-dropdown-btn:hover { opacity: .88; }
  .tab-dropdown-menu {
    position: absolute; top: calc(100% + 6px); left: 0;
    background: #fff; border: 1px solid #e4e6ea; border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,.12); min-width: 180px;
    z-index: 100; display: none; overflow: hidden;
  }
  .tab-dropdown-menu.open { display: block; }
  .tab-option {
    display: flex; align-items: center; gap: 10px;
    padding: 11px 14px; font-size: 0.83rem; cursor: pointer;
    transition: background .12s; border: none; background: none; width: 100%; text-align: left;
  }
  .tab-option:hover { background: var(--gl); }
  .tab-option.active { background: var(--gl); color: var(--g); font-weight: 700; }
  .tab-option-icon { width: 28px; height: 28px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; flex-shrink: 0; }
  .tab-badge { margin-left: auto; background: #ff4444; color: #fff; border-radius: 10px; padding: 1px 6px; font-size: 0.68rem; font-weight: 700; }

  /* 채팅 메시지 */
  #chat-box { flex: 1; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 10px; scroll-behavior: smooth; min-height: 0; }
  #chat-box::-webkit-scrollbar { width: 3px; }
  #chat-box::-webkit-scrollbar-thumb { background: #ddd; border-radius: 3px; }

  .msg-row { display: flex; gap: 8px; align-items: flex-end; }
  .msg-row.me { flex-direction: row-reverse; }
  .msg-av { width: 28px; height: 28px; border-radius: 50%; background: var(--gb); color: var(--g); display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0; }
  .msg-inner { max-width: 68%; }
  .msg-name { font-size: 0.7rem; color: #999; margin-bottom: 2px; }
  .me .msg-name { text-align: right; }
  .msg-bbl { padding: 9px 13px; border-radius: 14px; font-size: 0.84rem; line-height: 1.5; word-break: break-word; }
  .msg-row:not(.me) .msg-bbl { background: #f2f3f5; color: #222; border-bottom-left-radius: 4px; }
  .me .msg-bbl { background: var(--g); color: #fff; border-bottom-right-radius: 4px; }
  .msg-time { font-size: 0.68rem; color: #bbb; margin-top: 2px; }
  .me .msg-time { text-align: right; }

  /* 입력창 */
  .chat-input-area { padding: 10px; border-top: 1px solid #f0f2f4; background: #fafbfc; flex-shrink: 0; }
  .input-wrap { display: flex; gap: 8px; align-items: flex-end; }
  #msg-input { flex: 1; border: 1px solid #e0e0e0; border-radius: 22px; padding: 9px 16px; font-size: 0.84rem; resize: none; max-height: 100px; outline: none; background: #fff; transition: border-color .15s; }
  #msg-input:focus { border-color: var(--g); }
  .send-btn { width: 38px; height: 38px; border-radius: 50%; background: var(--g); border: none; color: #fff; display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0; transition: opacity .15s; }
  .send-btn:hover { opacity: .85; }

  /* 왼쪽 패널 */
  .res-item { display: flex; align-items: center; gap: 8px; padding: 7px 8px; border-radius: 8px; cursor: pointer; text-decoration: none; color: inherit; font-size: 0.81rem; transition: background .12s; }
  .res-item:hover { background: var(--gl); color: inherit; }
  .res-av { width: 30px; height: 30px; border-radius: 50%; background: var(--g); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0; }
  .online-dot { width: 8px; height: 8px; border-radius: 50%; background: #28a745; flex-shrink: 0; }
  .sec-label { font-size: 0.68rem; color: #aaa; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; padding: 10px 4px 5px; }
  .grp-item { display: flex; align-items: center; gap: 7px; padding: 6px 8px; border-radius: 8px; font-size: 0.8rem; text-decoration: none; color: inherit; transition: background .12s; }
  .grp-item:hover { background: var(--gl); color: inherit; }
  .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 4px; }
  .stat-box { background: #f8f9fa; border-radius: 8px; padding: 8px; text-align: center; }
  .stat-n { font-size: 1.1rem; font-weight: 700; color: var(--g); }
  .stat-l { font-size: 0.68rem; color: #999; }

  /* 오른쪽 패널 */
  .info-sec { margin-bottom: 14px; }
  .info-sec-title { font-size: 0.68rem; color: #aaa; font-weight: 700; letter-spacing: .03em; margin-bottom: 6px; padding: 0 2px; }
  .info-card { display: block; background: #f8f9fa; border-radius: 9px; padding: 9px 11px; margin-bottom: 5px; font-size: 0.79rem; text-decoration: none; color: inherit; transition: background .12s; }
  .info-card:hover { background: #eef7f2; color: inherit; }
  .info-card-t { font-weight: 600; color: #222; margin-bottom: 1px; font-size: 0.8rem; }
  .info-card-s { color: #999; font-size: 0.73rem; }

  /* 온보딩 카드 */
  .onboard-card { background: linear-gradient(135deg, #f0fdf6 0%, #e8f5ee 100%); border: 1px solid #c3e6d0; border-radius: 12px; padding: 16px; margin-bottom: 10px; }
  .onboard-step { display: flex; align-items: flex-start; gap: 10px; padding: 8px 0; border-bottom: 1px solid #d4edda; }
  .onboard-step:last-child { border-bottom: none; padding-bottom: 0; }
  .step-num { width: 24px; height: 24px; border-radius: 50%; background: var(--g); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0; margin-top: 1px; }
  .step-text { font-size: 0.8rem; color: #333; line-height: 1.5; }
  .step-text strong { color: var(--g); }
  .step-link { display: inline-block; margin-top: 4px; font-size: 0.75rem; color: var(--g); text-decoration: none; font-weight: 600; }
  .step-link:hover { text-decoration: underline; }

  /* 빈 상태 안내 */
  .empty-state { text-align: center; padding: 30px 16px; }
  .empty-icon { font-size: 2.2rem; margin-bottom: 10px; }
  .empty-title { font-size: 0.9rem; font-weight: 700; color: #444; margin-bottom: 6px; }
  .empty-desc { font-size: 0.78rem; color: #888; line-height: 1.6; margin-bottom: 14px; }
  .empty-btn { display: inline-block; padding: 7px 18px; background: var(--g); color: #fff; border-radius: 20px; font-size: 0.8rem; font-weight: 600; text-decoration: none; transition: opacity .15s; }
  .empty-btn:hover { opacity: .85; color: #fff; }
  .empty-btn-outline { display: inline-block; padding: 6px 16px; border: 1.5px solid var(--g); color: var(--g); border-radius: 20px; font-size: 0.78rem; font-weight: 600; text-decoration: none; margin-left: 6px; transition: background .15s; }
  .empty-btn-outline:hover { background: var(--gl); color: var(--g); }

  /* 추천 봉사 카드 */
  .suggest-card { background: #fff; border: 1px solid #e4e6ea; border-radius: 10px; padding: 10px 12px; margin-bottom: 6px; display: flex; align-items: center; gap: 10px; text-decoration: none; color: inherit; transition: border-color .15s, box-shadow .15s; }
  .suggest-card:hover { border-color: var(--gb); box-shadow: 0 2px 8px rgba(26,122,74,.1); color: inherit; }
  .suggest-icon { width: 36px; height: 36px; border-radius: 10px; background: var(--gl); color: var(--g); display: flex; align-items: center; justify-content: center; font-size: 1rem; flex-shrink: 0; }

  /* 뷰 전환 */
  .chat-view { flex: 1; overflow: hidden; display: flex; flex-direction: column; min-height: 0; }
  .chat-view.hidden { display: none; }
  .scroll-view { flex: 1; overflow-y: auto; padding: 14px; }
  .scroll-view::-webkit-scrollbar { width: 3px; }
  .scroll-view::-webkit-scrollbar-thumb { background: #ddd; border-radius: 3px; }
</style>

</head>
<body>
<nav class="navbar navbar-expand-lg sticky-top" style="background:#1a7a4a;box-shadow:0 1px 4px rgba(0,0,0,.2);padding:0 12px;min-height:52px;">
  <div class="container-fluid px-0">

    <!-- 브랜드 -->
    <a class="navbar-brand fw-bold text-white d-flex align-items-center gap-2" href="/" style="font-size:1rem;">
      <i class="fas fa-home"></i>해솔7 지킴이
    </a>

    <!-- 모바일 햄버거 -->
    <button class="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#mainNav"
            style="color:#fff;font-size:1.2rem;padding:4px 8px;">
      <i class="fas fa-bars"></i>
    </button>

    <div class="collapse navbar-collapse" id="mainNav">
      <!-- 메인 메뉴 -->
      <ul class="navbar-nav me-auto align-items-lg-center" style="gap:2px;">
        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle text-white d-flex align-items-center gap-1" href="#"
             data-bs-toggle="dropdown" style="font-size:0.82rem;">
            <i class="fas fa-comments"></i>채팅
          </a>
          <ul class="dropdown-menu" style="background:#1a7a4a;border:none;box-shadow:0 4px 12px rgba(0,0,0,.3);min-width:130px;">
            <li><a class="dropdown-item text-white d-flex align-items-center gap-2" href="/chat/public/" style="font-size:0.82rem;"><i class="fas fa-comments"></i>전체채팅</a></li>
            <li><a class="dropdown-item text-white d-flex align-items-center gap-2" href="/chat/dm/list/" style="font-size:0.82rem;"><i class="fas fa-comment-dots"></i>1:1 채팅</a></li>
            <li><a class="dropdown-item text-white d-flex align-items-center gap-2" href="/groups/" style="font-size:0.82rem;"><i class="fas fa-users"></i>소모임채팅</a></li>
          </ul>
        </li>
        <li class="nav-item"><a class="nav-link text-white d-flex align-items-center gap-1" href="/letters/" style="font-size:0.82rem;"><i class="fas fa-envelope"></i>쪽지</a></li>
        <li class="nav-item"><a class="nav-link text-white d-flex align-items-center gap-1" href="/boards/" style="font-size:0.82rem;"><i class="fas fa-clipboard-list"></i>게시판</a></li>
        <li class="nav-item"><a class="nav-link text-white d-flex align-items-center gap-1" href="/surveys/" style="font-size:0.82rem;"><i class="fas fa-poll"></i>설문</a></li>
        <li class="nav-item"><a class="nav-link text-white d-flex align-items-center gap-1" href="/volunteer/" style="font-size:0.82rem;"><i class="fas fa-calendar-alt"></i>봉사</a></li>
        <li class="nav-item"><a class="nav-link text-white d-flex align-items-center gap-1" href="/notices/" style="font-size:0.82rem;"><i class="bi bi-bell"></i>공지</a></li>
        <li class="nav-item"><a class="nav-link text-white d-flex align-items-center gap-1" href="/complaints/" style="font-size:0.82rem;"><i class="bi bi-megaphone"></i>민원</a></li>
        <li class="nav-item"><a class="nav-link text-white d-flex align-items-center gap-1" href="/community/docs/" style="font-size:0.82rem;"><i class="fas fa-file-alt"></i>관리문서</a></li>
        <li class="nav-item"><a class="nav-link text-white d-flex align-items-center gap-1" href="/stats/" style="font-size:0.82rem;"><i class="fas fa-chart-bar"></i>통계</a></li>
        <li class="nav-item">
          <form method="get" action="/search/" class="d-flex align-items-center ms-1">
            <div class="d-flex align-items-center" style="background:rgba(255,255,255,.15);border-radius:20px;height:30px;overflow:hidden;">
              <input type="text" name="q" placeholder="검색..." class="border-0 bg-transparent text-white px-2" style="font-size:0.78rem;width:100px;outline:none;">
              <button type="submit" class="border-0 bg-transparent text-white px-2"><i class="fas fa-search" style="font-size:0.75rem;"></i></button>
            </div>
          </form>
        </li>
      </ul>

      <!-- 우측 사용자 메뉴 -->
      <ul class="navbar-nav align-items-lg-center" style="gap:4px;">
        
          <li class="nav-item"><a class="nav-link text-white" href="/accounts/login/" style="font-size:0.82rem;">로그인</a></li>
          <li class="nav-item"><a class="nav-link fw-bold" href="/accounts/signup/" style="font-size:0.82rem;background:rgba(255,255,255,.2);border-radius:8px;padding:4px 12px;color:#fff;">회원가입</a></li>
        
      </ul>
    </div>
  </div>
</nav>


<div class="layout">

  <!-- ① 왼쪽: 입주민 & 소모임 -->
  <div class="panel panel-left">
    <div class="ph"><p class="ph-title"><i class="fas fa-users me-1" style="color:var(--g)"></i>입주민</p></div>
    <div class="pb">
      <div class="sec-label">온라인</div>
      
      <a href="/chat/dm/5/" class="res-item">
        <div class="res-av">노</div>
        <div style="flex:1;min-width:0;">
          <div style="font-weight:600;font-size:0.81rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">노귀현</div>
          <div style="font-size:0.7rem;color:#999;">713동 0704호</div>
        </div>
        <div class="online-dot" title="온라인"></div>
      </a>
      
      <a href="/chat/dm/1/" class="res-item">
        <div class="res-av">H</div>
        <div style="flex:1;min-width:0;">
          <div style="font-weight:600;font-size:0.81rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">haesol7</div>
          <div style="font-size:0.7rem;color:#999;">입주민</div>
        </div>
        <div class="online-dot" title="온라인"></div>
      </a>
      
      <a href="/chat/dm/4/" class="res-item">
        <div class="res-av">N</div>
        <div style="flex:1;min-width:0;">
          <div style="font-weight:600;font-size:0.81rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">nunlove</div>
          <div style="font-size:0.7rem;color:#999;">720동 호</div>
        </div>
        <div class="online-dot" title="온라인"></div>
      </a>
      
      <a href="/chat/dm/3/" class="res-item">
        <div class="res-av">H</div>
        <div style="flex:1;min-width:0;">
          <div style="font-weight:600;font-size:0.81rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">halos80</div>
          <div style="font-size:0.7rem;color:#999;">713동 1804호</div>
        </div>
        <div class="online-dot" title="온라인"></div>
      </a>
      
      <a href="/chat/dm/2/" class="res-item">
        <div class="res-av">A</div>
        <div style="flex:1;min-width:0;">
          <div style="font-weight:600;font-size:0.81rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">admin</div>
          <div style="font-size:0.7rem;color:#999;">입주민</div>
        </div>
        <div class="online-dot" title="온라인"></div>
      </a>
      

      <div class="sec-label">소모임</div>
      <a href="/groups/create/" class="grp-item" style="background:var(--gl);color:var(--g);font-weight:700;margin-bottom:4px;">
        <i class="fas fa-plus" style="font-size:0.75rem;"></i>소모임 만들기
      </a>
      
      <div style="font-size:0.75rem;color:#ccc;padding:4px 4px 0;text-align:center;">소모임 없음</div>
      

      <div class="sec-label" style="margin-top:8px;">단지 현황</div>
      <div class="stat-grid">
        <div class="stat-box"><div class="stat-n">0</div><div class="stat-l">소모임</div></div>
        <div class="stat-box"><div class="stat-n">0</div><div class="stat-l">활동</div></div>
        <div class="stat-box"><div class="stat-n">0</div><div class="stat-l">승인</div></div>
        <div class="stat-box"><div class="stat-n">0</div><div class="stat-l">배지</div></div>
      </div>
    </div>
  </div>

  <!-- 중앙: 커뮤니티 대시보드 -->
  <div class="panel" style="flex:1;overflow-y:auto;">
    <div class="ph" style="background:#fafbfc;">
      <div style="display:flex;align-items:center;justify-content:space-between;">
        <span class="ph-title">🏘️ 해솔7단지 지금 이 순간</span>
        <span style="font-size:0.72rem;color:#aaa;">실시간 현황</span>
      </div>
    </div>
    <div class="pb" style="padding:12px;display:flex;flex-direction:column;gap:12px;">

      <!-- 단지 현황 숫자 -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;">
        <div class="stat-box"><div style="font-size:1.3rem;font-weight:700;color:var(--g);">5</div><div style="font-size:0.7rem;color:#888;">전체 회원</div></div>
        <div class="stat-box"><div style="font-size:1.3rem;font-weight:700;color:#1a7a4a;">0</div><div style="font-size:0.7rem;color:#888;">인증 입주민</div></div>
        <div class="stat-box"><div style="font-size:1.3rem;font-weight:700;color:#e67e22;">0</div><div style="font-size:0.7rem;color:#888;">활성 소모임</div></div>
        <div class="stat-box"><div style="font-size:1.3rem;font-weight:700;color:#e74c3c;">0</div><div style="font-size:0.7rem;color:#888;">봉사 완료</div></div>
      </div>

      <!-- 긴급/고정 공지 -->
      

      <!-- 인기 게시글 -->
      <div>
        <div style="font-size:0.75rem;font-weight:700;color:#888;margin-bottom:6px;display:flex;align-items:center;gap:4px;">
          <i class="bi bi-fire text-warning"></i> 이번주 인기 게시글
          <a href="/boards/" style="margin-left:auto;font-size:0.72rem;color:var(--g);text-decoration:none;">전체보기</a>
        </div>
        
        <div style="text-align:center;color:#ccc;font-size:0.78rem;padding:10px;">아직 인기 게시글이 없어요</div>
        
      </div>

      <!-- 진행중인 설문 -->
      

      <!-- 최근 전체채팅 미리보기 -->
      <div>
        <div style="font-size:0.75rem;font-weight:700;color:#888;margin-bottom:6px;display:flex;align-items:center;gap:4px;">
          <i class="bi bi-chat-dots-fill text-success"></i> 실시간 채팅
          <a href="/chat/public/" style="margin-left:auto;font-size:0.72rem;color:var(--g);text-decoration:none;">채팅 참여하기</a>
        </div>
        <div style="background:#f8f9fa;border-radius:10px;padding:8px;">
          
          <div style="display:flex;align-items:flex-start;gap:7px;margin-bottom:7px;">
            <div class="msg-av"></div>
            <div style="flex:1;min-width:0;">
              <div style="font-size:0.72rem;color:#888;"></div>
              <div style="font-size:0.8rem;color:#333;">아직 기능이 정상 동작하는 상황은 아니라서 채팅 게시물이나 통계 설문 …</div>
            </div>
            <div style="font-size:0.68rem;color:#bbb;flex-shrink:0;">14:29</div>
          </div>
          
          <div style="display:flex;align-items:flex-start;gap:7px;margin-bottom:7px;">
            <div class="msg-av"></div>
            <div style="flex:1;min-width:0;">
              <div style="font-size:0.72rem;color:#888;"></div>
              <div style="font-size:0.8rem;color:#333;">테스트 중입니다.</div>
            </div>
            <div style="font-size:0.68rem;color:#bbb;flex-shrink:0;">14:28</div>
          </div>
          
        </div>
      </div>

      <!-- 봉사활동 일정 -->
      

      <!-- 비로그인 가입 유도 -->
      
      <div style="background:linear-gradient(135deg,#1a7a4a,#2ecc71);border-radius:12px;padding:16px;text-align:center;color:#fff;">
        <div style="font-size:1rem;font-weight:700;margin-bottom:6px;">해솔7단지 이웃이신가요?</div>
        <div style="font-size:0.8rem;opacity:.9;margin-bottom:12px;">가입하고 이웃들과 소통해보세요!</div>
        <div style="display:flex;gap:8px;justify-content:center;">
          <a href="/accounts/signup/" style="background:#fff;color:var(--g);padding:7px 16px;border-radius:20px;font-size:0.8rem;font-weight:700;text-decoration:none;">회원가입</a>
          <a href="/accounts/login/" style="background:rgba(255,255,255,.2);color:#fff;padding:7px 16px;border-radius:20px;font-size:0.8rem;font-weight:600;text-decoration:none;border:1px solid rgba(255,255,255,.4);">로그인</a>
        </div>
      </div>
      

    </div>
  </div>
  <div class="panel panel-right">
    <div class="ph"><p class="ph-title"><i class="fas fa-th-large me-1" style="color:var(--g)"></i>정보 패널</p></div>
    <div class="pb">

      <!-- 공지 -->
      <div class="info-sec">
        <div class="info-sec-title">📢 최신 공지</div>
        
        <div class="info-card" style="color:#bbb;text-align:center;cursor:default;">
          <div style="font-size:1rem;margin-bottom:4px;">📭</div>
          <div style="font-size:0.75rem;">새 공지가 없어요</div>
        </div>
        
        <a href="/boards/" style="font-size:0.73rem;color:var(--g);display:block;text-align:right;text-decoration:none;margin-top:2px;">전체 게시판 →</a>
      </div>

      <!-- 관리 문서 -->
      <div class="info-sec">
        <div class="info-sec-title">📋 관리 문서</div>
        
        <a href="/community/docs/1/" class="info-card">
          <div class="info-card-t">관리규약</div>
          <div class="info-card-s">법률 정보</div>
        </a>
        
      </div>

      <!-- 봉사 일정 -->
      <div class="info-sec">
        <div class="info-sec-title">🌿 봉사 일정</div>
        
        <!-- 봉사 없을 때 추천 -->
        <div style="font-size:0.75rem;color:#999;margin-bottom:8px;padding:0 2px;">예정된 일정이 없어요.<br>이런 활동은 어떨까요?</div>
        <a href="/volunteer/" class="suggest-card">
          <div class="suggest-icon">🌳</div>
          <div>
            <div style="font-size:0.8rem;font-weight:600;color:#333;">단지 환경 정비</div>
            <div style="font-size:0.72rem;color:#999;">쾌적한 단지를 함께 만들어요</div>
          </div>
        </a>
        <a href="/volunteer/" class="suggest-card">
          <div class="suggest-icon">🐕</div>
          <div>
            <div style="font-size:0.8rem;font-weight:600;color:#333;">펫 매너 캠페인</div>
            <div style="font-size:0.72rem;color:#999;">반려동물 에티켓을 함께해요</div>
          </div>
        </a>
        <a href="/volunteer/" class="suggest-card">
          <div class="suggest-icon">🌙</div>
          <div>
            <div style="font-size:0.8rem;font-weight:600;color:#333;">야간 안전 순찰</div>
            <div style="font-size:0.72rem;color:#999;">안전한 단지를 지켜요</div>
          </div>
        </a>
        <a href="/volunteer/" style="font-size:0.73rem;color:var(--g);display:block;text-align:center;text-decoration:none;margin-top:6px;font-weight:600;">+ 봉사 일정 만들기</a>
        
        
      </div>

      <!-- AI 안내 -->
      <div class="info-sec">
        <div class="info-sec-title">🤖 AI 안내</div>
        <a href="/chatbot/" class="info-card" style="background:#eef7f2;border:1px solid #c3e6d0;">
          <div class="info-card-t" style="color:var(--g);">관리규약 AI 질문</div>
          <div class="info-card-s">주차·펫·소음 등 궁금한 점을<br>AI에게 바로 물어보세요!</div>
        </a>
      </div>

      <!-- 내 정보 -->
      
      <div class="info-sec">
        <div class="info-card" style="text-align:center;cursor:default;">
          <div style="font-size:0.85rem;font-weight:600;color:#333;margin-bottom:8px;">함께 참여해요! 🏘️</div>
          <div style="font-size:0.75rem;color:#888;margin-bottom:10px;">로그인하면 채팅·봉사·소모임<br>모든 기능을 이용할 수 있어요.</div>
          <a href="/accounts/login/" style="display:block;background:var(--g);color:#fff;border-radius:8px;padding:7px;font-size:0.8rem;font-weight:600;text-decoration:none;margin-bottom:6px;">로그인</a>
          <a href="/accounts/signup/" style="display:block;border:1.5px solid var(--g);color:var(--g);border-radius:8px;padding:6px;font-size:0.8rem;font-weight:600;text-decoration:none;">회원가입</a>
        </div>
      </div>
      

    </div>
  </div>

</div>


  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    // 알림 카운트 갱신
    
  </script>
  
<script>
const PUBLIC_URL = "/chat/public/messages/";
const IS_AUTH = false;
let lastId = 0, polling = null;
let currentTab = 'public';

const tabMeta = {
  public:  { label: '전체 채팅',  icon: 'fa-globe',   desc: '단지 전체 입주민과 자유롭게 대화하세요' },
  dm:      { label: '1:1 쪽지',   icon: 'fa-envelope', desc: '이웃과 개인 대화를 나눠보세요' },
  group:   { label: '소모임 채팅', icon: 'fa-users',   desc: '소모임 멤버들과 대화하세요' },
  members: { label: '참여자 목록', icon: 'fa-list',    desc: '입주민 전체 목록을 확인하세요' },
};

function toggleDropdown() {
  document.getElementById('tabMenu').classList.toggle('open');
}
document.addEventListener('click', e => {
  if (!document.getElementById('tabDropdown').contains(e.target))
    document.getElementById('tabMenu').classList.remove('open');
});

function switchTab(tab) {
  currentTab = tab;
  document.getElementById('tabMenu').classList.remove('open');

  // 버튼 표시 업데이트
  const meta = tabMeta[tab];
  document.getElementById('tabIcon').className = 'fas ' + meta.icon;
  document.getElementById('tabLabel').textContent = meta.label;
  document.getElementById('tabDesc').textContent = meta.desc;

  // 옵션 active
  Object.keys(tabMeta).forEach(k => document.getElementById('opt-' + k)?.classList.remove('active'));
  document.getElementById('opt-' + tab)?.classList.add('active');

  // 뷰 전환
  ['public','dm','group','members'].forEach(v => {
    const el = document.getElementById('view-' + v);
    if (el) el.classList.toggle('hidden', v !== tab);
  });

  // 폴링 제어
  if (tab === 'public') {
    if (!polling && IS_AUTH) polling = setInterval(fetchMessages, 3000);
  } else {
    clearInterval(polling); polling = null;
  }
}

function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');
}

function renderMsgs(msgs) {
  const box = document.getElementById('chat-box');
  const atBot = box.scrollHeight - box.scrollTop <= box.clientHeight + 60;
  msgs.forEach(m => {
    const d = document.createElement('div');
    d.className = 'msg-row' + (m.is_me ? ' me' : '');
    d.innerHTML = `
      <div class="msg-av">${esc(m.author.charAt(0).toUpperCase())}</div>
      <div class="msg-inner">
        <div class="msg-name">${esc(m.author)}${m.unit ? ' · ' + esc(m.unit) : ''}</div>
        <div class="msg-bbl">${esc(m.message)}</div>
        <div class="msg-time">${m.time}</div>
      </div>`;
    box.appendChild(d);
    lastId = Math.max(lastId, m.id);
  });
  if (atBot) box.scrollTop = box.scrollHeight;
}

async function fetchMessages() {
  if (!IS_AUTH) return;
  try {
    const res = await fetch(PUBLIC_URL + '?since=' + lastId);
    const data = await res.json();
    const box = document.getElementById('chat-box');
    if (data.pinned && data.pinned.length > 0 && typeof renderPinned === 'function') renderPinned(data.pinned);
    if (data.messages && data.messages.length > 0) {
      if (lastId === 0) box.innerHTML = '';
      renderMsgs(data.messages);
    } else if (lastId === 0) {
      box.innerHTML = '<div class="empty-state">' +
        '<div class="empty-icon">💬</div>' +
        '<div class="empty-title">아직 대화가 없어요</div>' +
        '<div class="empty-desc">우리 단지 첫 대화의 주인공이 되어보세요!<br>이웃에게 인사를 건네보는 건 어떨까요? 😊</div>' +
        '</div>';
    }
  } catch(e) {}
}

async function sendMessage() {
  const inp = document.getElementById('msg-input');
  const msg = inp.value.trim();
  if (!msg) return;
  inp.value = ''; inp.style.height = 'auto';
  try {
    const fd = new FormData();
    fd.append('message', msg);
    fd.append('csrfmiddlewaretoken', 'hYdHhCdg7i6SJns6CrRqWl2SYXxZ6ofyexow36gfO52E6KeUU7Z6uyPm4CJIyiKj');
    await fetch(PUBLIC_URL, { method: 'POST', body: fd });
    fetchMessages();
  } catch(e) {}
}

const inp = document.getElementById('msg-input');
if (inp) {
  inp.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 100) + 'px';
  });
  inp.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
}

// 초기화
if (IS_AUTH) {
  fetchMessages();
  polling = setInterval(fetchMessages, 3000);
}
</script>

<script>
document.addEventListener('click', function(e) {
  const wrap = document.getElementById('user-menu-wrap');
  if (wrap && !wrap.contains(e.target)) {
    const dd = document.getElementById('user-dd');
    if (dd) dd.style.display = 'none';
  }
});
</script>
</body>
</html>
