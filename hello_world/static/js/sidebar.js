// 사이드바 섹션 폴딩 - 아코디언 방식 (하나만 열림)
const SB_SECS = ['sec-chat','sec-record','sec-together','sec-news','sec-myact','sec-admin'];

function toggleSection(id) {
  const target = document.getElementById(id);
  if (!target) return;
  const isOpen = !target.classList.contains('folded');

  // 모두 닫기
  SB_SECS.forEach(sid => {
    const sec = document.getElementById(sid);
    const label = sec ? sec.previousElementSibling : null;
    if (sec) { sec.classList.add('folded'); sec.style.maxHeight = '0'; }
    if (label) label.classList.add('folded');
    localStorage.setItem('sb_fold_' + sid, '1');
  });

  // 클릭한 것이 닫혀있었으면 열기
  if (isOpen) {
    target.classList.remove('folded');
    target.style.maxHeight = target.scrollHeight + 'px';
    const label = target.previousElementSibling;
    if (label) label.classList.remove('folded');
    localStorage.setItem('sb_fold_' + id, '0');
  }
}

// 페이지 로드시 상태 복원
document.addEventListener('DOMContentLoaded', function() {
  // 2개 이상 열려있으면 초기화
  let openCount = SB_SECS.filter(id => localStorage.getItem('sb_fold_'+id) === '0').length;
  if (openCount > 1) SB_SECS.forEach(id => localStorage.removeItem('sb_fold_'+id));

  SB_SECS.forEach(id => {
    const sec = document.getElementById(id);
    const label = sec ? sec.previousElementSibling : null;
    if (!sec) return;
    if (localStorage.getItem('sb_fold_'+id) === '0') {
      sec.classList.remove('folded');
      sec.style.maxHeight = sec.scrollHeight + 'px';
      if (label) label.classList.remove('folded');
    } else {
      sec.classList.add('folded');
      sec.style.maxHeight = '0';
      if (label) label.classList.add('folded');
    }
  });
});
