package app.teum.memo;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Map;

/** Local, bundled UI; no remote scripts or arbitrary navigation in the native container. */
public final class MainActivity extends Activity {
    private WebView web;
    private String exportContent;
    private String appScheme;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.rgb(242,243,236));
        getWindow().setNavigationBarColor(Color.rgb(250,250,247));
        getWindow().getDecorView().setSystemUiVisibility(android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | android.view.View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        web = new WebView(this);
        appScheme = (getApplicationInfo().flags & android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE) != 0 ? "http" : "https";
        web.setBackgroundColor(Color.rgb(250,250,247));
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(false);
        web.getSettings().setAllowContentAccess(false);
        web.getSettings().setMixedContentMode(android.webkit.WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        web.setOnApplyWindowInsetsListener((view,insets) -> {
            view.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            return insets;
        });
        web.addJavascriptInterface(new ExportBridge(), "TeumExport");
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !("memo.local".equals(request.getUrl().getHost()) && appScheme.equals(request.getUrl().getScheme()));
            }
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (!"memo.local".equals(uri.getHost())) return null;
                String path = uri.getPath();
                if (path == null || path.equals("/")) path = "/index.html";
                Map<String,String> types = Map.of("/index.html","text/html","/app.js","text/javascript","/style.css","text/css","/icon.svg","image/svg+xml","/manifest.webmanifest","application/manifest+json");
                if (!types.containsKey(path)) return new WebResourceResponse("text/plain","UTF-8",404,"Not Found",Map.of(),new ByteArrayInputStream(new byte[0]));
                try {
                    return new WebResourceResponse(types.get(path),"UTF-8",200,"OK",Map.of("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src https: http://10.0.2.2:* http://127.0.0.1:* http://localhost:*; img-src 'self' data:; base-uri 'none'; form-action 'self'"),getAssets().open(path.substring(1)));
                } catch (IOException error) { return new WebResourceResponse("text/plain","UTF-8",new ByteArrayInputStream(new byte[0])); }
            }
        });
        setContentView(web);
        if (state == null || web.restoreState(state) == null) web.loadUrl(appScheme+"://memo.local/index.html?server=http%3A%2F%2F10.0.2.2%3A8910");
    }
    private final class ExportBridge {
        @JavascriptInterface public void save(String content, String name, String mime) {
            if (content.length() > 8_000_000) return;
            runOnUiThread(() -> {
                exportContent = content;
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType(mime.split(";")[0]).putExtra(Intent.EXTRA_TITLE,name);
                startActivityForResult(intent,41);
            });
        }
    }
    @Override protected void onActivityResult(int request, int result, Intent intent) {
        super.onActivityResult(request,result,intent);
        if (request != 41 || result != RESULT_OK || intent == null || intent.getData() == null || exportContent == null) return;
        try (var output = getContentResolver().openOutputStream(intent.getData())) {
            if (output == null) throw new IOException("No output");
            output.write(exportContent.getBytes(StandardCharsets.UTF_8));
            Toast.makeText(this,"메모를 내보냈어요.",Toast.LENGTH_SHORT).show();
        } catch (IOException error) { Toast.makeText(this,"내보내지 못했습니다. 다시 시도해 주세요.",Toast.LENGTH_LONG).show(); }
        finally { exportContent = null; }
    }
    @Override protected void onSaveInstanceState(Bundle state) { web.saveState(state); super.onSaveInstanceState(state); }
    @Override public void onBackPressed() {
        web.evaluateJavascript("(function(){for(const id of ['confirm-dialog','account-dialog']){const d=document.getElementById(id);if(d.open){d.close('cancel');return true;}}if(!document.getElementById('editor').hidden){document.getElementById('back').click();return true;}return false;})()", handled -> {
            if (!"true".equals(handled)) MainActivity.super.onBackPressed();
        });
    }
    @Override protected void onDestroy() { web.removeJavascriptInterface("TeumExport"); web.destroy(); super.onDestroy(); }
}
