#!/bin/bash
# Monitor scraping progress

echo "================================================================================"
echo "ANBIMA SCRAPING PROGRESS MONITOR"
echo "================================================================================"
echo ""

# Get latest log file
LOGFILE=$(ls -t logs/scraper_parallel_*.log 2>/dev/null | head -1)

if [ -z "$LOGFILE" ]; then
    echo "❌ No log file found"
    exit 1
fi

echo "📋 Log file: $LOGFILE"
echo ""

# Extract progress info
echo "📊 PROGRESS:"
tail -100 "$LOGFILE" | grep "Overall Progress" | tail -1
echo ""

echo "✅ RECENT SUCCESSES (last 5):"
tail -200 "$LOGFILE" | grep "✓ Successfully scraped" | tail -5
echo ""

echo "❌ RECENT FAILURES (last 5):"
tail -200 "$LOGFILE" | grep "Failed to scrape" | tail -5 || echo "  (none)"
echo ""

echo "⚠️  RATE LIMIT WARNINGS:"
grep -c "Rate limit detected" "$LOGFILE" && grep "Rate limit detected" "$LOGFILE" | tail -3 || echo "  ✓ No rate limiting detected"
echo ""

echo "📈 STATISTICS:"
SUCCESS_COUNT=$(grep -c "✓ Successfully scraped" "$LOGFILE")
FAILED_COUNT=$(grep -c "Failed to scrape" "$LOGFILE")
TOTAL=$((SUCCESS_COUNT + FAILED_COUNT))
if [ $TOTAL -gt 0 ]; then
    SUCCESS_RATE=$(echo "scale=1; $SUCCESS_COUNT * 100 / $TOTAL" | bc)
    echo "  Completed: $TOTAL/51 CNPJs"
    echo "  Success: $SUCCESS_COUNT (${SUCCESS_RATE}%)"
    echo "  Failed: $FAILED_COUNT"
else
    echo "  Starting..."
fi
echo ""

echo "================================================================================"
echo "Last update: $(date)"
echo "================================================================================"
