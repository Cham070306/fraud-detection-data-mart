# ERD - PaySim Fraud Detection Data Mart

`	ext
stg.TransactionRaw
  (BatchID, RowNumberInChunk) PK
          |
          v
 dim.DimDate (DateKey) ---------------------+
 dim.DimTime (TimeKey) ---------------------+
 dim.DimTransactionType (TransactionTypeKey)+
 dim.DimAccount (AccountKey) ---------------+--> fact.FactTransaction (TransactionKey PK)
 dim.DimAmountBand (AmountBandKey) ---------+       DateKey FK
                                                    TimeKey FK
                                                    TransactionTypeKey FK
                                                    OrigAccountKey FK
                                                    DestAccountKey FK
                                                    AmountBandKey FK
                                                    StepRaw, Amount, balances, IsFraud, IsFlaggedFraud
                                                             |
                                                             +--> fact.FactModelScore (ScoreKey PK)
                                                             |        TransactionKey FK
                                                             |        ModelVersionKey FK
                                                             |        RiskPolicyKey FK
                                                             |        DateKey FK
                                                             |
                                                             +--> fact.FactAlert (AlertKey PK)
                                                                      TransactionKey FK
                                                                      ScoreKey FK
                                                                      RiskPolicyKey FK
                                                                      DateKey FK

dim.DimRiskPolicy (RiskPolicyKey) ----------> fact.FactModelScore
                                           \-> fact.FactAlert

dim.DimModelVersion (ModelVersionKey) -----> fact.FactModelScore
`
