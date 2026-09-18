const { STAGE1_SYSTEM_PROMPT, readCorpus, callOpenRouter } = require("./_shared");

module.exports = async (req, res) => {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  try {
    const { design, hyde_doc } = req.body;
    if (!design || !hyde_doc) return res.status(400).json({ error: "design and hyde_doc are required" });

    const corpus = readCorpus("stage1.txt");
    const userMessage =
      `${corpus}\n\n===== HYPOTHETICAL REGULATORY FRAMING (context only) =====\n\n${hyde_doc}` +
      `\n\n===== ENGINEER'S DESIGN DESCRIPTION =====\n\n${design}`;

    const { text, usage } = await callOpenRouter(STAGE1_SYSTEM_PROMPT, userMessage, 16000);
    res.status(200).json({ report: text, usage });
  } catch (e) {
    res.status(500).json({ error: String(e.message || e) });
  }
};

module.exports.config = { maxDuration: 300 };
