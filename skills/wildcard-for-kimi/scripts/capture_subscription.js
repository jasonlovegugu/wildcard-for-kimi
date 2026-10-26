// Wildcard · for KIMI Talk — 套餐与有效期截取（Kimi WebBridge evaluate 注入执行）
// 只返回 plan / valid_until，不读取整页文本，不返回用量、账单或历史订单。

(async () => {
  const SUB_PATH = "/settings/subscription";
  const TIER_RE = /\b(Allegretto|Allegro|Moderato|Andante|Max|Plus|Pro|Go)\b/i;
  const MAX_TEXT_NODES = 160;

  if (!/(^|\.)kimi\.com$/i.test(location.hostname)) {
    return { status: "wrong_page", url: location.origin + location.pathname, note: "not_on_kimi_domain" };
  }

  const matchPlan = (value) => {
    const match = value.match(TIER_RE);
    return match ? match[1] : null;
  };

  const readMembership = () => {
    const fields = { plan: null, valid_until: null };
    const root = document.querySelector("main") || document.body;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let dateNode = null;
    let sawLogin = false;
    let seen = 0;

    while (walker.nextNode() && seen < MAX_TEXT_NODES) {
      const value = (walker.currentNode.nodeValue || "").trim();
      if (!value) continue;
      seen += 1;
      if (/登录|注册|sign in/i.test(value)) sawLogin = true;
      if (!fields.plan) fields.plan = matchPlan(value);
      if (!dateNode && /有效期至?/.test(value)) dateNode = walker.currentNode.parentElement;
      if (fields.plan && dateNode) break;
    }

    let container = dateNode;
    for (let depth = 0; container && depth < 3; depth += 1, container = container.parentElement) {
      const text = (container.textContent || "").trim();
      if (!text || text.length > 240) continue;
      if (!fields.valid_until) {
        const match = text.match(/有效期至[:：]?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})/);
        if (match) fields.valid_until = match[1];
      }
      if (!fields.plan) fields.plan = matchPlan(text);
      if (fields.plan && fields.valid_until) break;
    }

    return {
      fields,
      sawLogin,
      complete: Boolean(fields.plan && fields.valid_until),
      foundMembership: Boolean(fields.plan || fields.valid_until),
    };
  };

  let result = readMembership();
  const deadline = Date.now() + 10000;
  while (!result.complete && !result.sawLogin && Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, 200));
    result = readMembership();
  }

  if (!result.foundMembership && result.sawLogin) {
    return { status: "needs_login", url: location.origin + location.pathname };
  }
  if (!location.pathname.startsWith(SUB_PATH) && !result.foundMembership) {
    return { status: "wrong_page", url: location.origin + location.pathname, note: "path_changed" };
  }

  return {
    status: "ok",
    url: location.origin + location.pathname,
    captured_at: new Date().toISOString(),
    fields: result.fields,
  };
})()
