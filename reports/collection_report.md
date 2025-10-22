# 采集器覆盖度巡检报告

生成时间：2025-10-22T10:02:20.722213+00:00

| 分组 | 类别 | 平台 | 来源 | 状态 | 详情 |
| --- | --- | --- | --- | --- | --- |
| social_sources | influencers | X | official_api_or_nitter | 失败 | 采集异常: CollectorError: <urlopen error Tunnel connection failed: 403 Forbidden> |
| social_sources | influencers | Telegram | public_channels | 失败 | 采集异常: CollectorError: <urlopen error Tunnel connection failed: 403 Forbidden> |
| social_sources | influencers | Lens/Farcaster | graph/subgraph | 失败 | 采集异常: CollectorError: <urlopen error Tunnel connection failed: 403 Forbidden> |
| social_sources | media_kols | YouTube/TikTok | channels | 失败 | 采集异常: CollectorError: <urlopen error Tunnel connection failed: 403 Forbidden> |
| social_sources | dev_communities | Discord (public) | servers | 失败 | 采集异常: CollectorError: <urlopen error Tunnel connection failed: 403 Forbidden> |
| social_sources | forums | Reddit | subreddits | 失败 | 采集异常: CollectorError: <urlopen error Tunnel connection failed: 403 Forbidden> |
| social_sources | cn_social | Weibo/Wechat | accounts/feeds | 失败 | 采集异常: CollectorError: <urlopen error Tunnel connection failed: 403 Forbidden> |
| news_sources | crypto_portals | Web/RSS | CoinDesk | 失败 | 采集异常: CollectorError: <urlopen error Tunnel connection failed: 403 Forbidden> |
| news_sources | crypto_portals | Web/RSS | Cointelegraph | 失败 | 采集异常: CollectorError: <urlopen error Tunnel connection failed: 403 Forbidden> |
| news_sources | mainstream_media | Web/RSS | Bloomberg/Reuters/FT/WSJ/CNBC | 失败 | 采集异常: CollectorError: <urlopen error Tunnel connection failed: 403 Forbidden> |
| research_sources | institutional_research | Web/API | Messari/Delphi/Galaxy/Glassnode_research | 失败 | 采集异常: CollectorError: <urlopen error Tunnel connection failed: 403 Forbidden> |
| exchange_market_feeds | cex_market_ws | WS/API | Binance/OKX/Bybit/Deribit/Coinbase | 失败 | 采集异常: ConfigurationError: Market endpoint for 'ticker/trades/oi/funding/liquidations' missing in EARMATE_MARKET_SNAPSHOTS |
| exchange_market_feeds | exchange_status | Status/API | statuspages_of_exchanges | 失败 | 采集异常: CollectorError: <urlopen error Tunnel connection failed: 403 Forbidden> |
| onchain_metrics | onchain_core | Node/API | self_nodes_or_providers | 失败 | 采集异常: CollectorError: <urlopen error Tunnel connection failed: 403 Forbidden> |
| onchain_metrics | stablecoin_flows | API | USDT/USDC issuers & explorers | 失败 | 采集异常: CollectorError: <urlopen error Tunnel connection failed: 403 Forbidden> |
| regulation_policy | regulators | Web/RSS | SEC/CFTC/FED/USTreasury/ECB/BoE/MAS/FINMA | 失败 | 采集异常: ConfigurationError: RSS alias 'sec.gov/news/pressreleases' missing and not a URL |
| regulation_policy | courts_enforcement | Docs/RSS | PACER/court_feeds/law_firms_statements | 失败 | 未注册采集器: No collector registered for platform='Docs/RSS' category='courts_enforcement' |
| project_ecosystem | project_announcements | Blog/GitHub/Medium | official_feeds | 失败 | 未注册采集器: No collector registered for platform='Blog/GitHub/Medium' category='project_announcements' |
| project_ecosystem | community_forums | Forums | Bitcointalk/Ethereum Magicians/Project Forums | 失败 | 未注册采集器: No collector registered for platform='Forums' category='community_forums' |
| project_ecosystem | dao_governance | Snapshot/Forum | Aave/Uniswap/MakerDAO/...  | 失败 | 未注册采集器: No collector registered for platform='Snapshot/Forum' category='dao_governance' |
| macro_sources | macro_calendar | Calendars/API | CPI/PPI/Jobs/FOMC/DXY/Yields | 失败 | 未注册采集器: No collector registered for platform='Calendars/API' category='macro_calendar' |
