from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import (ResearchWorkspace, ResearchReport, Paper, Claim, ClaimEvidence,
                        ResearchInsight, FutureReview, AgenticWorkflowRun)

class ResearchWorkspaceService:
    def __init__(self, db: Session): self.db = db

    def _workspace(self, w):
        if not w: return None
        papers = self.db.query(Paper).filter(Paper.id.in_(w.paper_ids or [])).all() if w.paper_ids else []
        return {"id":w.id,"title":w.title,"description":w.description,"research_question":w.research_question,
                "paper_ids":w.paper_ids or [],"papers":[{"id":p.id,"filename":p.filename,"pages":p.pages,"chunks":p.chunks} for p in papers],
                "created_at":w.created_at,"updated_at":w.updated_at,
                "report_count":self.db.query(ResearchReport).filter_by(workspace_id=w.id).count()}

    def list_workspaces(self):
        return [self._workspace(w) for w in self.db.query(ResearchWorkspace).order_by(desc(ResearchWorkspace.updated_at)).all()]

    def get_workspace(self, wid): return self._workspace(self.db.get(ResearchWorkspace,wid))

    def create_workspace(self, data):
        ids=list(dict.fromkeys(data.paper_ids or []))
        if ids:
            found={p.id for p in self.db.query(Paper).filter(Paper.id.in_(ids)).all()}
            missing=set(ids)-found
            if missing: raise ValueError(f"Unknown paper IDs: {', '.join(sorted(missing))}")
        w=ResearchWorkspace(id=str(uuid4()),title=data.title.strip(),description=data.description,
                           research_question=data.research_question,paper_ids=ids)
        self.db.add(w); self.db.commit(); self.db.refresh(w); return self._workspace(w)

    def update_workspace(self,wid,data):
        w=self.db.get(ResearchWorkspace,wid)
        if not w: return None
        vals=data.model_dump(exclude_unset=True)
        if "paper_ids" in vals:
            ids=list(dict.fromkeys(vals["paper_ids"] or []))
            found={p.id for p in self.db.query(Paper).filter(Paper.id.in_(ids)).all()} if ids else set()
            if set(ids)-found: raise ValueError("One or more selected papers do not exist.")
            vals["paper_ids"]=ids
        for k,v in vals.items(): setattr(w,k,v)
        w.updated_at=datetime.now(timezone.utc); self.db.commit(); self.db.refresh(w); return self._workspace(w)

    def delete_workspace(self,wid):
        w=self.db.get(ResearchWorkspace,wid)
        if not w:return False
        self.db.query(ResearchReport).filter_by(workspace_id=wid).delete()
        self.db.delete(w); self.db.commit(); return True

    def generate_report(self,wid,opts):
        w=self.db.get(ResearchWorkspace,wid)
        if not w: return None
        papers=self.db.query(Paper).filter(Paper.id.in_(w.paper_ids or [])).all() if w.paper_ids else []
        claims=self.db.query(Claim).filter(Claim.paper_id.in_(w.paper_ids or [])).all() if w.paper_ids and opts.include_claims else []
        evidence_by_claim={}
        if claims:
            ev=self.db.query(ClaimEvidence).filter(ClaimEvidence.claim_id.in_([c.id for c in claims])).all()
            for e in ev: evidence_by_claim.setdefault(e.claim_id,[]).append({"quote":e.quote,"page":e.page_number,"chunk_id":e.chunk_id,"kind":e.evidence_kind})
        selected_claim_ids={c.id for c in claims}
        insights=[]
        if opts.include_insights and selected_claim_ids:
            insights=[i for i in self.db.query(ResearchInsight).order_by(desc(ResearchInsight.created_at)).limit(100).all()
                      if selected_claim_ids.intersection(i.supporting_claim_ids or [])]
        reviews=[]
        if opts.include_reviews and selected_claim_ids:
            reviews=[r for r in self.db.query(FutureReview).order_by(desc(FutureReview.created_at)).limit(100).all()
                     if selected_claim_ids.intersection(r.supporting_claim_ids or [])]
        review_ids={r.id for r in reviews}
        workflows=[]
        if opts.include_workflows and review_ids:
            workflows=self.db.query(AgenticWorkflowRun).filter(AgenticWorkflowRun.future_review_id.in_(review_ids)).order_by(desc(AgenticWorkflowRun.created_at)).limit(20).all()
        manifest=[{"paper_id":p.id,"filename":p.filename,"pages":p.pages} for p in papers]
        sections=[
          {"heading":"Abstract","content":f"This report organizes research material for: {w.research_question or w.title}. It includes {len(papers)} selected papers and {len(claims)} extracted claims. This is a generated workspace synthesis, not a systematic review."},
          {"heading":"Research Context and Question","content":w.description+(("\nResearch question: "+w.research_question) if w.research_question else "")},
          {"heading":"Included Literature","items":[{"paper_id":p.id,"filename":p.filename,"pages":p.pages,"chunks":p.chunks} for p in papers]},
          {"heading":"Evidence-Linked Claims","items":[{"claim_id":c.id,"paper_id":c.paper_id,"claim":c.claim_text,"type":c.claim_type,"confidence":c.confidence,"limitations":c.limitations,"evidence":evidence_by_claim.get(c.id,[])} for c in claims]},
          {"heading":"Research Intelligence (AI-Generated Hypotheses)","items":[{"title":i.title,"description":i.description,"rationale":i.rationale,"supporting_claim_ids":i.supporting_claim_ids,"confidence":i.confidence} for i in insights]},
          {"heading":"Future Reviewer Assessments (AI-Generated)","items":[{"id":r.id,"title":r.research_title,"novelty":r.novelty_assessment,"methodology":r.methodology_review,"weaknesses":r.weaknesses,"suggestions":r.improvement_suggestions,"supporting_claim_ids":r.supporting_claim_ids} for r in reviews]},
          {"heading":"Agentic Workflow History (AI-Generated Analysis)","items":[{"id":a.id,"request":a.user_request,"status":a.status,"summary":a.summary,"tools":[x.get("tool") for x in (a.results or [])]} for a in workflows]},
          {"heading":"Limitations and Verification Notes","content":"Claims and quoted evidence in this report are retrieved from the selected papers and stored claim graph. Research Intelligence, Future Reviewer and Agentic Workflow sections are AI-generated analyses and should be independently checked. Absence of a claim in this collection does not establish a global research gap. Confirm all quotations, page numbers, methods and references against the original PDFs before publication."},
        ]
        report=ResearchReport(id=str(uuid4()),workspace_id=wid,title=(opts.title or f"{w.title} — Research Report").strip(),sections=sections,source_manifest=manifest)
        self.db.add(report); w.updated_at=datetime.now(timezone.utc); self.db.commit(); self.db.refresh(report)
        return self._report(report)

    def _report(self,r): return {"id":r.id,"workspace_id":r.workspace_id,"title":r.title,"sections":r.sections,"source_manifest":r.source_manifest,"created_at":r.created_at}
    def list_reports(self,wid): return [self._report(r) for r in self.db.query(ResearchReport).filter_by(workspace_id=wid).order_by(desc(ResearchReport.created_at)).all()]
    def get_report(self,rid): return self._report(self.db.get(ResearchReport,rid))
