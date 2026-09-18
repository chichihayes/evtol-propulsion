const { HYDE_SYSTEM_PROMPT, callOpenRouter, HYDE_MODEL } = require("./_shared");

module.exports = async (req, res) => {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  try {
    const { design } = req.body;
    if (!design || !design.trim()) return res.status(400).json({ error: "design is required" });
    const { text, usage } = await callOpenRouter(HYDE_SYSTEM_PROMPT, design, 4000, HYDE_MODEL);
    res.status(200).json({ hyde_doc: text, usage });
  } catch (e) {
    res.status(500).json({ error: String(e.message || e) });
  }
};
