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
    if (paper.note) {
        const noteTag = document.createElement('span');
        noteTag.className = 'paper-tag note';
        noteTag.textContent = 'Note';
        noteTag.onclick = () => {
            // Create popup card
            const popup = document.createElement('div');
            popup.className = 'note-popup';
            
            // Create card content
            const card = document.createElement('div');
            card.className = 'note-card';
            
            // Add close button
            const closeBtn = document.createElement('span');
            closeBtn.className = 'note-close';
            closeBtn.textContent = '×';
            closeBtn.onclick = (e) => {
                e.stopPropagation();
                popup.remove();
            };
            
            // Add note content
            const content = document.createElement('p');
            content.textContent = paper.note;
            
            // Assemble card
            card.appendChild(closeBtn);
            card.appendChild(content);
            popup.appendChild(card);
            
            // Add to document
            document.body.appendChild(popup);
            
            // Close when clicking outside
            popup.onclick = (e) => {
                if (e.target === popup) {
                    popup.remove();
                }
            };
        };
        tagsDiv.appendChild(noteTag);
    }

    // BibTeX tag
    if (paper.bibtex) {
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
    }

    // Survey tag (if available)
    if (paper.surveyTag) {
        const surveyTag = document.createElement('span');
        surveyTag.className = 'paper-tag survey';
        surveyTag.textContent = paper.surveyTag;
        surveyTag.title = 'This paper is included in our survey';
        tagsDiv.appendChild(surveyTag);
    }

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