function createPaperReference(paper) {
    const paperDiv = document.createElement('div');
    paperDiv.className = 'paper-reference';

    // Title with link
    const titleDiv = document.createElement('div');
    titleDiv.className = 'paper-title';
    const titleLink = document.createElement('a');
    titleLink.href = paper.link;
    titleLink.textContent = paper.title;
    titleDiv.appendChild(titleLink);
    paperDiv.appendChild(titleDiv);

    // Tags container
    const tagsDiv = document.createElement('div');
    tagsDiv.className = 'paper-tags';

    // Venue tag
    const venueTag = document.createElement('span');
    venueTag.className = 'paper-tag venue';
    venueTag.textContent = paper.venue;
    tagsDiv.appendChild(venueTag);

    // Code tag (if available)
    if (paper.code) {
        const codeTag = document.createElement('a');
        codeTag.className = 'paper-tag code';
        codeTag.href = paper.code;
        codeTag.textContent = 'Code';
        codeTag.target = '_blank';
        tagsDiv.appendChild(codeTag);
    }

    // Note tag
    const noteTag = document.createElement('span');
    noteTag.className = 'paper-tag note';
    noteTag.textContent = 'Note';
    noteTag.setAttribute('data-note', paper.note);
    tagsDiv.appendChild(noteTag);

    // BibTeX tag
    const bibtexTag = document.createElement('span');
    bibtexTag.className = 'paper-tag bibtex';
    bibtexTag.textContent = 'BibTeX';
    bibtexTag.onclick = () => {
        navigator.clipboard.writeText(paper.bibtex).then(() => {
            const originalText = bibtexTag.textContent;
            bibtexTag.textContent = 'Copied!';
            setTimeout(() => {
                bibtexTag.textContent = originalText;
            }, 2000);
        });
    };
    tagsDiv.appendChild(bibtexTag);

    paperDiv.appendChild(tagsDiv);
    return paperDiv;
}

// Example usage:
// const paper = {
//     title: "REEF: Representation Encoding Fingerprints for Large Language Models",
//     link: "https://arxiv.org/abs/2410.14273",
//     venue: "ICLR 2025 Oral",
//     code: "https://github.com/AI45Lab/REEF",
//     note: "利用模型激活特征来作为指纹",
//     bibtex: "@article{zhang2024reef,\n  title={REEF: Representation Encoding Fingerprints for Large Language Models},\n  author={Zhang, Jie and Liu, Dongrui and Qian, Chen and Zhang, Linfeng and Liu, Yong and Qiao, Yu and Shao, Jing},\n  journal={arXiv preprint arXiv:2410.14273},\n  year={2024}\n}"
// };
// document.getElementById('papers-container').appendChild(createPaperReference(paper)); 