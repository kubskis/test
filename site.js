(function(){
  var dot=document.getElementById('dot'), st=document.getElementById('st');
  function set(c,t){if(dot){dot.className='dot '+c;st.textContent=t}}
  fetch('/api/status',{cache:'no-store'}).then(function(r){return r.json()}).then(function(d){
    var ok=d&&d.ok&&(d.health==='ok'||d.bot==='up');set(ok?'ok':'bad',ok?'бот работает':'есть проблемы');
  }).catch(function(){set('bad','нет связи')});
  var b=document.getElementById('burger'), l=document.getElementById('links');
  if(b&&l){b.addEventListener('click',function(){var o=l.classList.toggle('open');b.setAttribute('aria-expanded',o)});
    l.addEventListener('click',function(e){if(e.target.tagName==='A')l.classList.remove('open')})}
})();
