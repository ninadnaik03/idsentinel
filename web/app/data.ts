export const models = [
  { id:"M3", name:"Semantic", accent:"cyan", accuracy:.590909, macro:.590038, classF1:[.413793,.689655,.666667], failures:18, params:"27,822,435", bestVal:.581, duration:"~3.4 min", weights:null, matrix:[[6,5,3],[3,10,1],[6,0,10]] },
  { id:"M4", name:"Semantic + Texture", accent:"violet", accuracy:.681818, macro:.678519, classF1:[.48,.888889,.666667], failures:14, params:"28,355,317", bestVal:.760, duration:"~3.1 min", weights:"Semantic 0.503779 · Texture 0.496221", matrix:[[6,1,7],[1,12,1],[4,0,12]] },
  { id:"M5", name:"Semantic + Edge", accent:"blue", accuracy:.636364, macro:.640249, classF1:[.48,.846154,.594595], failures:16, params:"28,329,333", bestVal:.760, duration:"~3.3 min", weights:"Semantic 0.502496 · Edge 0.497504", matrix:[[6,1,7],[0,11,3],[5,0,11]] },
];
export const classes=["BONA_FIDE","PRINT","SCREEN"];
export const nav=[
  ["/research","Research"],["/24-hours","24 Hours"],["/experiments","Experiments"],["/architecture","Architecture"],
  ["/methodology","Methodology"],["/failures","Failures"],["/demo","Demo"],["/about","About"]
];
