const { HYDE_SYSTEM_PROMPT, callOpenRouter } = require("./_shared");

module.exports = async (req, res) => {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  try {
    const { stage1_report } = req.body;
    if (!stage1_report) return res.status(400).json({ error: "stage1_report is required" });
    const { text, usage } = await callOpenRouter(HYDE_SYSTEM_PROMPT, stage1_report, 4000);
    res.status(200).json({ hyde_doc: text, usage });
  } catch (e) {
    res.status(500).json({ error: String(e.message || e) });
  }
};
