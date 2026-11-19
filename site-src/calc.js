/* Vacancy cost calculator. initCalc("en") or initCalc("zh"); element ids are prefixed with the language. */
function initCalc(L){
  var $=function(id){return document.getElementById(L+"-"+id)};
  if(!$("form"))return;
  var zh=L==="zh";
  var v=function(k){var x=parseFloat(String($(k).value).replace(/,/g,""));return isFinite(x)&&x>=0?x:0};
  var rm=function(n){return(n<0?"-":"")+"RM "+Math.round(Math.abs(n)).toLocaleString("en-MY")};
  var r1=function(n){return Math.round(n*10)/10};
  var mo=function(n){return zh?r1(n)+" 个月":r1(n)+(r1(n)===1?" month":" months")};
  var INT=0.7;
  var CPY=zh?"复制 WhatsApp 文字":"Copy as WhatsApp message";
  $("copyBtn").textContent=CPY;
  function render(){
    var sel=document.querySelector('input[name="'+L+'-mkt"]:checked');
    var offer=v("offer"),exp=v("expect"),w=sel?+sel.value:3,freeO=v("freeO"),
        inst=v("inst"),feeM=v("fee"),sst=v("sst")/100,term=v("term")||12;
    var interest=inst*INT;
    $("intHint").innerHTML=zh
      ?"利息约 <b>"+rm(interest)+"</b> / 月（以供期的 70% 估算）"
      :"Interest ≈ <b>"+rm(interest)+"</b> / month (estimated at 70% of instalment)";
    // Same window for both options: wait + term. The offer tenant moves in now and renews at the same rent.
    var win=w+term;
    var rentO=offer*(win-freeO),feeO=offer*feeM*(1+sst),netO=rentO-feeO;
    var rentE=exp*term,feeE=exp*feeM*(1+sst),netE=rentE-feeE;
    var diff=netO-netE;
    var be=offer>0?(netE-(offer*(term-freeO)-feeO))/offer:0; // longest wait still worth it, in months
    $("cCash").textContent=rm(inst*w);
    $("cInt").textContent=rm(interest*w);
    var accept=diff>=0;
    [1,3,6,12].forEach(function(m){
      var d=(offer*(m+term-freeO)-feeO)-netE,b=$("b"+m);
      b.className="badge "+(d>=0?"good":"bad");
      b.textContent=d>=0?(zh?"接":"Accept"):(zh?"等":"Wait");
    });
    $("verdict").className="verdict "+(accept?"good":"bad");
    $("vBig").textContent=accept?(zh?"建议接受这个 Offer":"Recommended: accept the offer"):(zh?"建议不接，等期望租金":"Recommended: decline and wait");
    var sub;
    if(accept){
      if(be<=0)sub=zh?"就算明天就有期望租金的租客，也赢不过这个 Offer。":"Even if a tenant at your expected rent appeared tomorrow, this offer still comes out ahead.";
      else sub=zh
        ?"接 Offer 多拿 "+rm(diff)+"。期望租金的租客要在 "+mo(be)+"内出现才值得等，你预计要等 "+mo(w)+"。"
        :"Accepting earns "+rm(diff)+" more. Waiting only pays if a tenant at your expected rent shows up within "+mo(be)+"; you expect "+mo(w)+".";
    }else{
      sub=zh
        ?"等期望租金多拿 "+rm(-diff)+"，但 "+mo(be)+"内一定要租出去。超过这个时间，就应该接 Offer。"
        :"Waiting earns "+rm(-diff)+" more, but only if you rent it out within "+mo(be)+". Past that, take the offer.";
    }
    $("vSub").textContent=sub;
    var T=zh
      ?["同样算 "+mo(win),"接 Offer","等期望租金","空置（月）","免租装修期（月）","收到租金","中介费 + SST","净收入"]
      :["Over "+mo(win),"Accept","Wait","Vacant (months)","Free renovation (months)","Rent received","Agent fee + service tax","Net income"];
    $("tbl").innerHTML="<tr><th>"+T[0]+"</th><th>"+T[1]+"</th><th>"+T[2]+"</th></tr>"
      +"<tr><td>"+T[3]+'</td><td class="n">0</td><td class="n">'+r1(w)+"</td></tr>"
      +"<tr><td>"+T[4]+'</td><td class="n">'+r1(freeO)+'</td><td class="n">0</td></tr>'
      +"<tr><td>"+T[5]+'</td><td class="n">'+rm(rentO)+'</td><td class="n">'+rm(rentE)+"</td></tr>"
      +"<tr><td>"+T[6]+'</td><td class="n neg">'+rm(-feeO)+'</td><td class="n neg">'+rm(-feeE)+"</td></tr>"
      +'<tr class="total"><td>'+T[7]+'</td><td class="n '+(accept?"pos":"")+'">'+rm(netO)+'</td><td class="n '+(accept?"":"pos")+'">'+rm(netE)+"</td></tr>";
    $("tNote").textContent=zh
      ?"供期两边都要付，所以不放进比较。两边用同样 "+mo(win)+"来比，Offer 租约到期后假设同样租金续租。"
      :"Instalment is paid either way, so it is left out of the comparison. Both options cover the same "+mo(win)+"; the offer tenancy is assumed to renew at the same rent.";
    var offS=offer.toLocaleString("en-MY"),expS=exp.toLocaleString("en-MY");
    var sign="\n\nVictor Tai\nThe Roof Realty\n📲 +6017-775 7229";
    $("copyOut").value=zh
      ?"老板，帮你算了一下这个 offer 👇\n\n租客出价：RM "+offS+"（免租装修 "+mo(freeO)+"）\n你的期望：RM "+expS+"（预计还要空 "+mo(w)+"）\n\n再空 "+mo(w)+"，你自己要掏 "+rm(inst*w)+" 供期，其中大约 "+rm(interest*w)+" 是利息，拿不回的。\n\n扣掉免租期和中介费 + SST，同样算 "+mo(win)+"：\n• 接 offer：净收 "+rm(netO)+"\n• 等期望租金：净收 "+rm(netE)+"\n\n"
        +(accept?"👉 我建议接这个 offer，多拿 "+rm(diff)+"。"+(be>0?"\n除非 "+mo(be)+"内一定等得到 RM "+expS+" 的租客。":""):"👉 可以先不接，但 "+mo(be)+"内还没租出去，就应该接类似的 offer。")+sign
      :"Hi boss, here's the math on this offer 👇\n\nTenant offer: RM "+offS+" (free renovation "+mo(freeO)+")\nYour expected rent: RM "+expS+" (about "+mo(w)+" more vacant)\n\nWaiting "+mo(w)+" means paying "+rm(inst*w)+" in instalments yourself, about "+rm(interest*w)+" of it interest you never get back.\n\nAfter free renovation and agent fee + service tax, over the same "+mo(win)+":\n• Accept offer: net "+rm(netO)+"\n• Wait: net "+rm(netE)+"\n\n"
        +(accept?"👉 I recommend accepting this offer. You come out "+rm(diff)+" ahead."+(be>0?"\nUnless you're sure to get RM "+expS+" within "+mo(be)+".":""):"👉 You can hold for now, but if it's still empty after "+mo(be)+", take a similar offer.")+sign;
  }
  $("form").addEventListener("input",render);
  $("form").addEventListener("submit",function(e){e.preventDefault()});
  $("copyBtn").addEventListener("click",function(){
    var t=$("copyOut").value,b=$("copyBtn");
    var done=function(){b.textContent=zh?"已复制":"Copied";setTimeout(function(){b.textContent=CPY},1600)};
    var fb=function(){var ta=$("copyOut");ta.select();try{document.execCommand("copy")?done():(b.textContent=zh?"复制失败":"Copy failed")}catch(e){b.textContent=zh?"复制失败":"Copy failed"}};
    navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(t).then(done,fb):fb();
  });
  render();
}

/* Requirement brief: builds a WhatsApp link from the form. Nothing is sent or stored by the page. */
function initBrief(){
  var g=function(id){return document.getElementById("brief-"+id)};
  if(!g("form"))return;
  function upd(){
    var lines=["Hi Victor, I found you through your website.","","Looking to "+g("deal").value.toLowerCase()+": "+g("type").value];
    if(g("area").value.trim())lines.push("Area: "+g("area").value.trim());
    if(g("size").value.trim())lines.push("Size: "+g("size").value.trim());
    if(g("note").value.trim())lines.push("Notes: "+g("note").value.trim());
    g("send").href="https://wa.me/60177757229?text="+encodeURIComponent(lines.join("\n"));
  }
  g("form").addEventListener("input",upd);
  g("form").addEventListener("submit",function(e){e.preventDefault()});
  upd();
}

/* Homepage unit filter: All / Commercial / Industrial */
function initFilter(){
  document.querySelectorAll(".seg[aria-label='Filter units']").forEach(function(seg){
    var grid=seg.nextElementSibling;
    seg.addEventListener("click",function(e){
      var b=e.target.closest("button[data-f]");if(!b)return;
      seg.querySelectorAll("button").forEach(function(x){x.setAttribute("aria-pressed",String(x===b))});
      grid.querySelectorAll(".lcard").forEach(function(c){c.hidden=b.dataset.f!=="all"&&c.dataset.kind!==b.dataset.f});
    });
  });
}

/* Area tabs: Shops & offices / Factories & warehouses */
function initTabs(){
  document.querySelectorAll(".seg[role='tablist']").forEach(function(seg){
    var sec=seg.parentElement;
    seg.addEventListener("click",function(e){
      var b=e.target.closest("button[data-tab]");if(!b)return;
      seg.querySelectorAll("button").forEach(function(x){var on=x===b;x.setAttribute("aria-pressed",String(on));x.setAttribute("aria-selected",String(on))});
      sec.querySelectorAll("[data-group]").forEach(function(g){g.hidden=g.dataset.group!==b.dataset.tab});
    });
  });
}

/* play Facebook reels inside the page */
function initVideos(){
  document.querySelectorAll('a.vcard[data-fb]').forEach(function(a){
    a.addEventListener('click',function(e){
      e.preventDefault();
      var f=a.querySelector('.vframe'); if(f.querySelector('iframe'))return;
      var href=encodeURIComponent('https://www.facebook.com/reel/'+a.dataset.fb+'/');
      f.innerHTML='<iframe src="https://www.facebook.com/plugins/video.php?href='+href+'&show_text=false&autoplay=true&width=360" title="Facebook reel" allow="autoplay; encrypted-media; picture-in-picture; web-share" allowfullscreen></iframe>';
    });
  });
}
