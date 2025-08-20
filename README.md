<h1 align="center">🚀 Awesome LLM Copyright Protection</h1>

<p align="center"><b>
A curated collection of research and techniques for protecting the intellectual property of Large Language Models (LLMs), including watermarking, fingerprinting, and more.
</b></p>

<p align="center">
  <a href="https://xuzhenhua55.github.io/awesome-llm-copyright-protection/">
    <img src="https://img.shields.io/badge/📑-Survey_Paper-blue" alt="Survey Paper"/>
  </a>
  <a href="https://github.com/Xuzhenhua55/awesome-llm-copyright-protection">
    <img src="https://awesome.re/badge.svg" alt="Awesome"/>
  </a>
  <img src="https://img.shields.io/github/last-commit/Xuzhenhua55/awesome-llm-copyright-protection?color=green" alt="Last Commit"/>
  <img src="https://img.shields.io/badge/PRs-Welcome-red" alt="PRs Welcome"/>
  <img src="https://img.shields.io/github/stars/Xuzhenhua55/awesome-llm-copyright-protection?color=yellow" alt="Stars"/>
  <img src="https://img.shields.io/github/forks/Xuzhenhua55/awesome-llm-copyright-protection?color=lightblue" alt="Forks"/>
</p>

<hr/>

<h2>📝 Abstract</h2>

<p align="justify">
Copyright protection for large language models is of critical importance, given their substantial development costs, proprietary value, and potential for misuse. Existing surveys have predominantly focused on techniques for tracing LLM-generated content—namely, text watermarking—while a systematic exploration of methods for protecting the models themselves (i.e., model watermarking and model fingerprinting) remains absent. Moreover, the relationships and distinctions among text watermarking, model watermarking, and model fingerprinting have not been comprehensively clarified.
</p>

<p align="justify">
This work presents a comprehensive survey of the current state of LLM copyright protection technologies, with a focus on model fingerprinting, covering the following aspects: <b>(1)</b> clarifying the conceptual connection from text watermarking to model watermarking and fingerprinting, and adopting a unified terminology that incorporates model watermarking into the broader fingerprinting framework; <b>(2)</b> providing an overview and comparison of diverse text watermarking techniques, highlighting cases where such methods can function as model fingerprinting; <b>(3)</b> systematically categorizing and comparing existing model fingerprinting approaches for LLM copyright protection; <b>(4)</b> presenting, for the first time, techniques for fingerprint transfer and fingerprint removal; <b>(5)</b> summarizing evaluation metrics for model fingerprints, including effectiveness, harmlessness, robustness, stealthiness, and reliability; and <b>(6)</b> discussing open challenges and future research directions.
</p>

<p align="justify">
This survey aims to offer researchers a thorough understanding of both text watermarking and model fingerprinting technologies in the era of LLMs, thereby fostering further advances in protecting their intellectual property. We will continue to maintain and update this curated list of related papers and resources in this repository.
</p>

<hr/>

<h2>📖 Documentation</h2>

<div align="center">
  <table>
    <tr>
      <td align="center" width="50%">
        <h3>📄 Survey Paper</h3>
        <p><b><a href="https://arxiv.org/abs/2508.11548" target="_blank">Copyright Protection for Large Language Models: A Survey of Methods, Challenges, and Trends</a></b></p>
        <p><code>arXiv:2508.11548</code></p>
        <p><i>Comprehensive academic survey covering LLM copyright protection techniques</i></p>
      </td>
      <td align="center" width="50%">
        <h3>🌐 Interactive Website</h3>
        <p><b><a href="https://xuzhenhua55.github.io/awesome-llm-copyright-protection/" target="_blank">View Full Documentation & Papers</a></b></p>
        <p><code>GitHub Pages</code></p>
        <p><i>Interactive platform with organized papers, code links, and resources</i></p>
      </td>
    </tr>
  </table>
</div>

<p align="justify">
This project is a website version of our arXiv paper <a href="https://arxiv.org/abs/2508.11548" target="_blank">"Copyright Protection for Large Language Models: A Survey of Methods, Challenges, and Trends"</a>, aiming to provide a more interactive and accessible platform for researchers and practitioners in the field of LLM copyright protection. We begin with a comprehensive preliminary section that introduces essential background knowledge for understanding various LLM IP protection methods. We provide updated definitions of key concepts such as model watermarking and model fingerprinting in the context of 2025, enabling newcomers to clearly distinguish between these often-confused concepts.
</p>

<p align="justify">
Our ultimate goal is to present a comprehensive pipeline of copyright protection methods for large language models. From contemporary model fingerprint definitions to fingerprint embedding (and extraction) techniques, and from fingerprint transfer to removal strategies, we provide an end-to-end overview of the entire process.
</p>

<p align="justify">
🌟 This website serves as a valuable resource for researchers and practitioners, providing quick access to paper references, code links, and future resources for paper interpretation and analysis.
</p>

<hr/>

<h2>🗂️ Project Structure</h2>

<div align="center">
  <table>
    <tr>
      <td width="100%">
        <pre>
📚 <b>Preliminary</b>
   └─ Background Knowledge & Definitions

🔍 <b>Model Fingerprinting</b>
   ├─ <b>Non-invasive Fingerprinting</b>
   │    ├─ Parameter and Representation Based
   │    │    ├─ Parameter Space
   │    │    └─ Representation Features
   │    ├─ Semantic Feature Extraction
   │    └─ Adversarial Example-Based
   │
   └─ <b>Invasive Fingerprinting</b>
        ├─ Weight Watermark as Fingerprint
        └─ Backdoor Watermark as Fingerprint

🔄 <b>Fingerprint Transfer</b>
   └─ Cross-model Fingerprint Migration

🧹 <b>Fingerprint Removal</b>
   └─ Detection & Elimination Techniques
        </pre>
      </td>
    </tr>
  </table>
</div>

<hr/>

<h2>🌟 Features</h2>

<ul>
  <li><b>Comprehensive Survey:</b> Covers both classic and cutting-edge LLM copyright protection techniques.</li>
  <li><b>Systematic Categorization:</b> Clear taxonomy of fingerprinting and watermarking methods.</li>
  <li><b>Open Source & Community Driven:</b> Contributions and suggestions are welcome!</li>
</ul>

<hr/>

<h2>🤝 Contributing</h2>
<p>
We welcome contributions!<br>
Feel free to <a href="https://github.com/Xuzhenhua55/awesome-llm-copyright-protection/issues">open an issue</a> or submit a pull request.
</p>

<hr/>

<h2>📄 License</h2>
<p>
This project is licensed under the <a href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank">Creative Commons Attribution-NonCommercial 4.0 International License</a> (CC BY-NC 4.0). See the <a href="LICENSE" target="_blank">LICENSE</a> file for details.

Key terms:
- ✅ Share and adapt for non-commercial purposes
- ✅ Give appropriate credit to the original authors
- ✅ Provide a link to the license
- ✅ Indicate if changes were made
- ❌ No commercial use allowed
</p>

<hr/>


<h2>📖 Citation</h2>

<p>If you find our survey useful for your research, please consider citing:</p>

<details>
<summary><b>BibTeX</b></summary>

```bibtex
@misc{xu2025copyrightprotectionlargelanguage,
      title={Copyright Protection for Large Language Models: A Survey of Methods, Challenges, and Trends}, 
      author={Zhenhua Xu and Xubin Yue and Zhebo Wang and Qichen Liu and Xixiang Zhao and Jingxuan Zhang and Wenjun Zeng and Wengpeng Xing and Dezhang Kong and Changting Lin and Meng Han},
      year={2025},
      eprint={2508.11548},
      archivePrefix={arXiv},
      primaryClass={cs.CR},
      url={https://arxiv.org/abs/2508.11548}, 
}
```

</details>

<hr/>

<p align="center" style="font-size:1.1rem;">
  ⭐️ If you find this project helpful, please consider <a href="https://github.com/Xuzhenhua55/awesome-llm-copyright-protection" target="_blank"><b>starring us on GitHub</b></a>!<br>
  <b>For questions or suggestions:</b> <a href="mailto:xuzhenhua0326@zju.edu.cn">xuzhenhua0326@zju.edu.cn</a>
</p>
